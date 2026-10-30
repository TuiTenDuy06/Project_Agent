INSERT INTO stores (code, name, address, district, city, open_time, close_time, phone) VALUES
('Q1-01', 'Tiện Lợi 24h Nguyễn Huệ', '12 Nguyễn Huệ, Phường Bến Nghé', 'Quận 1', 'TP.HCM', '00:00', '23:59', '02811110001'),
('Q1-02', 'Tiện Lợi 24h Lê Lợi', '88 Lê Lợi, Phường Bến Thành', 'Quận 1', 'TP.HCM', '06:00', '23:00', '02811110002'),
('Q3-01', 'Tiện Lợi 24h Võ Văn Tần', '45 Võ Văn Tần, Phường 6', 'Quận 3', 'TP.HCM', '06:00', '22:00', '02811110003'),
('BT-01', 'Tiện Lợi 24h Xô Viết Nghệ Tĩnh', '201 Xô Viết Nghệ Tĩnh, Phường 17', 'Bình Thạnh', 'TP.HCM', '00:00', '23:59', '02811110004'),
('HK-01', 'Tiện Lợi 24h Hàng Bài', '30 Hàng Bài', 'Hoàn Kiếm', 'Hà Nội', '06:00', '23:00', '02422220001');

INSERT INTO products (sku, name, category, price) VALUES
('SP001', 'Sữa tươi Vinamilk không đường 1L', 'Sữa', 36000),
('SP002', 'Sữa tươi TH True Milk ít đường 180ml', 'Sữa', 9000),
('SP003', 'Bánh mì sandwich trứng', 'Đồ ăn nhanh', 15000),
('SP004', 'Cơm nắm cá ngừ', 'Đồ ăn nhanh', 18000),
('SP005', 'Mì ly Hảo Hảo tôm chua cay', 'Mì gói', 12000),
('SP006', 'Nước suối Aquafina 500ml', 'Nước uống', 6000),
('SP007', 'Cà phê sữa đá lon Highlands 235ml', 'Nước uống', 17000),
('SP008', 'Khăn giấy Pulppy 100 tờ', 'Gia dụng', 14000),
('SP009', 'Kem đánh răng P/S 180g', 'Chăm sóc cá nhân', 32000),
('SP010', 'Snack Oishi tôm cay 40g', 'Bánh kẹo', 7000);

-- Mỗi cửa hàng có tồn kho ngẫu nhiên từ 0 đến 50 cho mọi sản phẩm
INSERT INTO inventory (store_id, product_id, quantity)
SELECT s.id, p.id, floor(random() * 51)::int
FROM stores s CROSS JOIN products p;

INSERT INTO promotions (title, description, start_date, end_date) VALUES
('Combo sáng', 'Bánh mì sandwich + sữa tươi 180ml chỉ 20.000đ, áp dụng 6h-10h', CURRENT_DATE - 7, CURRENT_DATE + 30),
('Mua 2 tặng 1 mì ly', 'Mua 2 mì ly Hảo Hảo bất kỳ tặng 1 mì ly cùng loại', CURRENT_DATE - 3, CURRENT_DATE + 14),
('Giảm 10% hóa đơn từ 200.000đ', 'Dành cho thành viên hạng Bạc trở lên', CURRENT_DATE - 30, CURRENT_DATE - 1);
