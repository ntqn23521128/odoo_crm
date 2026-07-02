/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
// Import đúng đường dẫn chuẩn Odoo 19 (có components)
import { Navbar } from "@point_of_sale/app/components/navbar/navbar";
// Import hook chuẩn
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";

console.log(">>> [DEBUG] Reward Action Loaded (FULL VERSION: EMAIL + FIXES)");

patch(Navbar.prototype, {
    setup() {
        super.setup();
        this.pos = usePos();
        this.orm = useService("orm");
        this.notification = useService("notification");
    },

    async manualRedeem() {
        console.log(">>> [ACTION] Bắt đầu đổi thưởng...");

        // ---------------------------------------------------------
        // 1. LẤY ORDER
        // ---------------------------------------------------------
        const order = this.pos.getOrder();
        if (!order) {
            alert("⚠️ Chưa có đơn hàng nào.");
            return;
        }

        // ---------------------------------------------------------
        // 2. LẤY KHÁCH HÀNG (PARTNER)
        // ---------------------------------------------------------
        // Kiểm tra kỹ mọi trường hợp để không bị null
        const partner = order.partner || 
                        (typeof order.getPartner === 'function' ? order.getPartner() : null) ||
                        (typeof order.get_partner === 'function' ? order.get_partner() : null);

        if (!partner) {
            alert("⚠️ Vui lòng chọn khách hàng và bấm nút LƯU (Set Customer) trước!");
            return;
        }

        // ---------------------------------------------------------
        // 3. LẤY ĐIỂM TỪ SERVER (ORM READ)
        // ---------------------------------------------------------
        let currentPoints = 0;
        let cardId = null;

        try {
            const cards = await this.orm.searchRead(
                "loyalty.card",
                [["partner_id", "=", partner.id]], 
                ["points", "code"]
            );

            if (!cards || cards.length === 0) {
                alert(`⚠️ Khách ${partner.name} chưa có thẻ Loyalty.`);
                return;
            }

            currentPoints = cards[0].points || 0;
            cardId = cards[0].id;

        } catch (error) {
            console.error(error);
            alert("❌ Lỗi Server khi đọc điểm: " + error.message);
            return;
        }

        // Kiểm tra đủ điểm không
        if (currentPoints < 25) {
            alert(`⚠️ Thiếu điểm! Khách có ${currentPoints} (Cần 25).`);
            return;
        }

        // ---------------------------------------------------------
        // 4. LẤY MÓN ĐANG CHỌN & SẢN PHẨM
        // ---------------------------------------------------------
        const line = order.getSelectedOrderline();
        if (!line) {
            alert("⚠️ Vui lòng chọn món cần đổi thưởng.");
            return;
        }

        // FIX LỖI SẢN PHẨM: Dùng product_id (Odoo 19 Record)
        const product = line.product_id || line.product;

        if (!product) {
            alert("❌ Lỗi: Không đọc được thông tin sản phẩm (product_id missing).");
            return;
        }
        
        const productName = product.display_name || product.name || "Sản phẩm";

        // ---------------------------------------------------------
        // 5. XÁC NHẬN
        // ---------------------------------------------------------
        const confirmMsg = `🎁 XÁC NHẬN ĐỔI THƯỞNG + GỬI MAIL\n\n` +
                           `👤 Khách: ${partner.name}\n` +
                           `☕ Món: ${productName}\n` +
                           `⭐️ Trừ: 25 điểm (Còn: ${currentPoints - 25})\n\n` +
                           `Bạn có đồng ý không?`;

        if (!confirm(confirmMsg)) return;

        // ---------------------------------------------------------
        // 6. GỌI PYTHON ĐỂ XỬ LÝ (TRỪ ĐIỂM & GỬI MAIL)
        // ---------------------------------------------------------
        try {
            // Gọi hàm Python 'action_redeem_and_notify' trong model 'loyalty.card'
            const result = await this.orm.call(
                "loyalty.card",              
                "action_redeem_and_notify",  
                [],                          
                {                            
                    card_id: cardId,
                    points_to_deduct: 25,
                    product_name: productName
                }
            );

            // Kiểm tra kết quả trả về từ Python
            if (result && result.success) {
                
                // A. Cập nhật giao diện POS (Giảm giá về 0đ)
                // FIX LỖI SET GIÁ: Gán trực tiếp thuộc tính
                line.price_unit = 0;
                line.discount = 100;
                line.priceManuallySet = true;

                // Fallback cho một số bản cũ
                if (typeof line.set_unit_price === 'function') line.set_unit_price(0);

                const successMsg = `✅ Đã đổi & Gửi mail!\nĐiểm mới: ${result.new_points}`;
                
                if (this.notification) {
                     this.notification.add(successMsg, { type: "success" });
                } else {
                     alert(successMsg);
                }

            } else {
                // Nếu Python trả về False
                alert("❌ Lỗi Server: " + (result ? result.msg : "Không có phản hồi"));
            }

        } catch (error) {
            console.error(error);
            alert("❌ Lỗi kết nối (Vui lòng Restart Odoo): " + error.message);
        }
    },
});