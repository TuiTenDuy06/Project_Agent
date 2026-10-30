# Bài 15: Deploy lên VPS: tên miền, HTTPS, sao lưu

## Mục tiêu

Sau bài này, agent của bạn **chạy thật trên Internet** tại `https://cskh.<ten-mien-cua-ban>`. Cụ thể, bạn sẽ:

- Thuê VPS, đăng nhập bằng SSH key, **gia cố bảo mật** máy chủ.
- Trỏ **tên miền** về máy chủ.
- Chạy hệ thống bằng Docker Compose với **bí mật riêng cho production**.
- Cấu hình **Nginx** làm reverse proxy, có **rate limit**, và bật **HTTPS** miễn phí bằng Let's Encrypt.
- **Sao lưu database tự động** mỗi ngày và **thử khôi phục**.
- Hoàn thành **CD**: merge vào `main` là tự động deploy.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| Thiết lập máy chủ Ubuntu | [DigitalOcean: Initial Server Setup with Ubuntu](https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu) |
| SSH | [SSH Academy](https://www.ssh.com/academy/ssh) |
| DNS | [Cloudflare: What is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/) |
| UFW firewall | [Ubuntu: UFW](https://help.ubuntu.com/community/UFW) |
| Nginx reverse proxy | [Nginx: Beginner's Guide](https://nginx.org/en/docs/beginners_guide.html) |
| Rate limiting Nginx | [Nginx: Rate Limiting](https://blog.nginx.org/blog/rate-limiting-nginx) |
| Let's Encrypt / Certbot | [Certbot instructions](https://certbot.eff.org/instructions) |
| Cron | [crontab.guru](https://crontab.guru/), trang giải thích lịch cron |

---

## Phần lý thuyết

### 1. VPS là gì?

**VPS** (Virtual Private Server) là một máy tính ảo bạn thuê trong trung tâm dữ liệu, chạy 24/7, có **địa chỉ IP công khai**. Bạn điều khiển nó qua **SSH**.

### 2. Kiến trúc trên máy chủ

```
Internet
   │  cổng 443 (HTTPS), 80 (HTTP, tự chuyển sang HTTPS)
   ▼
┌─────────────── VPS (Ubuntu) ───────────────────────────────┐
│  UFW firewall: chỉ mở 22, 80, 443                           │
│                                                             │
│  Nginx (cài trực tiếp trên máy)                             │
│   - HTTPS (chứng chỉ Let's Encrypt)                         │
│   - Rate limit /chat                                        │
│   - Chặn /metrics                                           │
│        │ proxy tới 127.0.0.1:8080                           │
│        ▼                                                    │
│  Docker Compose                                             │
│   app :8080 ─── db :5432    prometheus :9090  grafana :3000 │
│   (tất cả chỉ nghe ở 127.0.0.1, không ra Internet)          │
└─────────────────────────────────────────────────────────────┘
```

### 3. Reverse proxy

**Nginx** đứng trước app, nhận mọi request từ Internet rồi chuyển vào app. Vì sao không cho app nhận trực tiếp?

- Nginx xử lý **HTTPS** hiệu quả và đã được kiểm chứng qua nhiều năm.
- Nginx làm **rate limit**, chặn đường dẫn nhạy cảm, giới hạn kích thước request.
- Sau này có thể chạy nhiều bản app phía sau một Nginx.

### 4. DNS và tên miền

**DNS** là "danh bạ" của Internet: nó đổi tên miền (`cskh.tienloi24h.vn`) thành địa chỉ IP (`203.0.113.10`). Bạn tạo một **bản ghi A** (A record) trỏ tên miền về IP của VPS.

### 5. HTTPS

**HTTPS** mã hóa dữ liệu giữa trình duyệt và máy chủ. Thiếu HTTPS, ai ở cùng mạng Wi-Fi quán cà phê cũng đọc được tin nhắn của khách. **Let's Encrypt** cấp chứng chỉ HTTPS **miễn phí**, tự gia hạn mỗi 90 ngày.

---

## Thực hành từng bước

### Phần A: Chuẩn bị (trên máy bạn)

#### Bước 1: Commit cấu hình Nginx và script sao lưu

Ta tạo sẵn các file cấu hình trong repository, để máy chủ chỉ việc `git pull` về.

```bash
cd ~/project_agent
```

```bash
mkdir -p deploy/nginx
```

Tạo file `deploy/nginx/agent.conf`:

```nginx
# Mỗi địa chỉ IP được gửi tối đa 10 tin nhắn mỗi phút vào /chat
limit_req_zone $binary_remote_addr zone=chat:10m rate=10r/m;

server {
    listen 80;
    server_name cskh.example.com;

    client_max_body_size 16k;

    # Metrics chỉ dành cho Prometheus trong mạng nội bộ
    location = /metrics {
        return 404;
    }

    location = /chat {
        limit_req zone=chat burst=5 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 90s;
    }

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Giải thích:

- **`limit_req_zone ... rate=10r/m`**: mỗi IP được 10 request mỗi phút. `zone=chat:10m` dành 10MB bộ nhớ để nhớ các IP (đủ cho khoảng 160.000 IP).
- **`limit_req zone=chat burst=5 nodelay`**: cho phép gửi dồn thêm 5 request (khách gõ nhanh vài câu liền). Vượt quá thì trả **429**. Trang chat ở Bài 09 đã xử lý mã này.
- **Vì sao cần rate limit?** Mỗi tin nhắn tốn tiền LLM. Không giới hạn, một kẻ xấu viết script gửi hàng nghìn tin/phút có thể **đốt hết ngân sách** của bạn trong vài giờ.
- **`client_max_body_size 16k`**: request lớn hơn 16KB bị từ chối ngay ở Nginx (tin nhắn tối đa 1000 ký tự, nên dư sức).
- **`location = /metrics { return 404; }`**: không ai từ Internet xem được metric.
- **`proxy_set_header ...`**: chuyển thông tin gốc (tên miền, IP thật của khách, giao thức http/https) cho app.
- **`proxy_read_timeout 90s`**: agent có thể mất vài chục giây khi gọi nhiều tool, nên cho chờ lâu hơn mặc định (60 giây).
- `server_name cskh.example.com` sẽ được sửa trên máy chủ.

Tạo file `deploy/backup.sh`:

```bash
#!/usr/bin/env bash
# Sao lưu database mỗi ngày, giữ 14 bản gần nhất, xóa hội thoại cũ hơn 90 ngày.
set -euo pipefail

cd "$(dirname "$0")/.."
BACKUP_DIR="$HOME/backups"
mkdir -p "$BACKUP_DIR"

docker compose exec -T db pg_dump -U agent agent | gzip > "$BACKUP_DIR/agent-$(date +%F).sql.gz"
find "$BACKUP_DIR" -name 'agent-*.sql.gz' -mtime +14 -delete

docker compose exec -T db psql -U agent -d agent -c \
    "DELETE FROM messages WHERE created_at < now() - interval '90 days';"

echo "$(date '+%F %T') sao lưu xong"
```

Giải thích:

- **`set -euo pipefail`**: dừng ngay khi có lệnh lỗi. `pipefail` đặc biệt quan trọng: không có nó, `pg_dump` lỗi nhưng `gzip` vẫn chạy thành công, và script tạo ra một file sao lưu **rỗng** mà bạn tưởng là tốt.
- **`cd "$(dirname "$0")/.."`**: chuyển về thư mục dự án, dù script được gọi từ đâu (cron chạy từ thư mục khác).
- **`pg_dump`**: xuất toàn bộ database ra các câu lệnh SQL, nén bằng `gzip`.
- **`find ... -mtime +14 -delete`**: xóa bản sao lưu cũ hơn 14 ngày để ổ đĩa không đầy.
- **`DELETE FROM messages ...`**: thực hiện chính sách lưu trữ dữ liệu cá nhân 90 ngày (Bài 08).

Cho phép chạy script:

```bash
chmod +x deploy/backup.sh
```

Commit (theo quy trình nhánh và PR của Bài 14):

```bash
git switch -c chuan-bi-deploy
```

```bash
git add deploy/
```

```bash
git commit -m "Bài 15: cấu hình Nginx và script sao lưu"
```

```bash
git push -u origin chuan-bi-deploy
```

Tạo PR, đợi CI xanh, Merge vào `main`.

#### Bước 2: Thuê VPS

Chọn một nhà cung cấp, ví dụ DigitalOcean, Vultr, Linode, Hetzner, hoặc các nhà cung cấp trong nước (BizFly Cloud, Viettel IDC, VNG Cloud…). Cấu hình đề nghị:

- **Hệ điều hành:** Ubuntu 24.04 LTS
- **Cấu hình:** 2 vCPU, 4GB RAM, 50GB SSD trở lên
- **Vùng (region):** Singapore hoặc Việt Nam (gần khách hàng, độ trễ thấp)
- **Xác thực:** chọn **SSH key**, dán nội dung `~/.ssh/id_ed25519.pub` (Bài 01). **Không** chọn mật khẩu.

Sau khi tạo, ghi lại **địa chỉ IP** của VPS. Trong bài, ta gọi nó là `<IP>`.

#### Bước 3: Trỏ tên miền

Mua tên miền ở nhà đăng ký (Mắt Bão, PA Vietnam, Namecheap, Cloudflare…). Nếu chỉ để học, có thể dùng tên miền phụ miễn phí như [DuckDNS](https://www.duckdns.org/).

Trong trang quản lý DNS, tạo bản ghi:

| Loại | Tên (Host) | Giá trị | TTL |
|---|---|---|---|
| A | `cskh` | `<IP>` | Auto / 300 |

Kiểm tra (có thể mất vài phút đến vài giờ để có hiệu lực):

```bash
nslookup cskh.<ten-mien-cua-ban>
```

Kết quả phải trả về đúng `<IP>`.

### Phần B: Thiết lập và gia cố máy chủ

#### Bước 4: Đăng nhập lần đầu và tạo user riêng

```bash
ssh root@<IP>
```

Gõ `yes` khi được hỏi về fingerprint. Bạn đang ở trong máy chủ, dấu nhắc đổi thành `root@...`.

Cập nhật hệ thống:

```bash
apt update && apt upgrade -y
```

Tạo user `deploy` để làm việc hằng ngày, **không dùng root**:

```bash
adduser deploy
```

Đặt mật khẩu mạnh và ghi nhớ (dùng cho `sudo`). Các câu hỏi khác nhấn Enter bỏ qua.

```bash
usermod -aG sudo deploy
```

Copy SSH key của root sang user `deploy`:

```bash
rsync --archive --chown=deploy:deploy ~/.ssh /home/deploy
```

**Mở một terminal mới trên máy bạn** (giữ nguyên phiên root hiện tại) và thử đăng nhập bằng `deploy`:

```bash
ssh deploy@<IP>
```

```bash
sudo whoami
```

Kết quả `root` nghĩa là `deploy` dùng được `sudo`. **Chỉ chuyển sang bước tiếp theo khi bước này thành công.**

#### Bước 5: Gia cố SSH

> ⚠️ **Cảnh báo:** bước này tắt đăng nhập bằng mật khẩu và tắt đăng nhập root. Làm sai thì bạn có thể **tự khóa mình ở ngoài máy chủ**. Luôn **giữ một phiên SSH đang mở** cho đến khi đã thử đăng nhập thành công bằng phiên mới. Nếu bị khóa, hầu hết nhà cung cấp VPS có "Web Console" trong trang quản lý để vào cứu.

Trong phiên `deploy`:

```bash
sudo nano /etc/ssh/sshd_config.d/99-hardening.conf
```

Gõ nội dung:

```
PasswordAuthentication no
PermitRootLogin no
```

Lưu bằng `Ctrl + O`, Enter, thoát bằng `Ctrl + X`. Kiểm tra cú pháp rồi khởi động lại SSH:

```bash
sudo sshd -t && sudo systemctl restart ssh
```

**Mở thêm một terminal mới** và thử:

```bash
ssh deploy@<IP>
```

Phải vào được. Thử tiếp `ssh root@<IP>`: phải bị từ chối (`Permission denied`). Giờ bạn có thể đóng phiên root cũ.

#### Bước 6: Bật firewall

```bash
sudo ufw allow OpenSSH
```

```bash
sudo ufw enable
```

Gõ `y` để xác nhận. Kiểm tra:

```bash
sudo ufw status
```

Chỉ có `OpenSSH` được phép. Cổng 80 và 443 sẽ mở ở Bước 11.

> ⚠️ **Cảnh báo về Docker và UFW:** Docker **tự thêm quy tắc firewall riêng, vượt qua UFW**. Nếu `compose.yaml` ghi `ports: "5432:5432"` (không có `127.0.0.1`), database sẽ mở ra Internet **dù UFW đã chặn**. Đó là lý do mọi `ports` trong dự án đều có tiền tố `127.0.0.1:`. Đừng bao giờ bỏ nó.

#### Bước 7: Tự động cài bản vá bảo mật

```bash
sudo apt install -y unattended-upgrades
```

```bash
sudo dpkg-reconfigure -plow unattended-upgrades
```

Chọn **Yes**. Máy chủ sẽ tự cài bản vá bảo mật hằng ngày.

#### Bước 8: Cài Docker

Làm theo [hướng dẫn chính thức cho Ubuntu](https://docs.docker.com/engine/install/ubuntu/), mục "Install using the apt repository". Sau đó cho user `deploy` dùng Docker không cần `sudo`:

```bash
sudo usermod -aG docker deploy
```

**Thoát ra** (`exit`) rồi **đăng nhập lại** để quyền mới có hiệu lực. Kiểm tra:

```bash
docker run --rm hello-world
```

```bash
docker compose version
```

### Phần C: Chạy ứng dụng

#### Bước 9: Lấy code về máy chủ

Máy chủ cần quyền **đọc** repository (nếu repository là private). Ta tạo một **deploy key**: SSH key chỉ có quyền đọc **một** repository.

Trên máy chủ:

```bash
ssh-keygen -t ed25519 -C "vps-deploy" -N "" -f ~/.ssh/id_ed25519
```

```bash
cat ~/.ssh/id_ed25519.pub
```

Copy dòng in ra. Trên GitHub: repository → **Settings** → **Deploy keys** → **Add deploy key**. Đặt tên "VPS", dán key, **không** tích "Allow write access". Bấm **Add key**.

Clone code:

```bash
cd ~
```

```bash
git clone git@github.com:<tai-khoan-github>/project_agent.git
```

```bash
cd project_agent
```

#### Bước 10: Tạo `.env` cho production

Tạo các mật khẩu ngẫu nhiên. Chạy lệnh sau **3 lần**, mỗi lần ghi lại một chuỗi (cho database, admin, Grafana):

```bash
openssl rand -hex 24
```

Tạo file `.env`:

```bash
nano .env
```

Nội dung (thay các giá trị trong `<...>`):

```bash
LLM_BASE_URL=https://generativelanguage.googleapis.com/v1beta/openai/
LLM_API_KEY=<API key dành riêng cho production>
LLM_MODEL=gemini-2.5-flash

POSTGRES_PASSWORD=<chuỗi ngẫu nhiên 1>
ADMIN_API_KEY=<chuỗi ngẫu nhiên 2>
GRAFANA_PASSWORD=<chuỗi ngẫu nhiên 3>
```

Không cần `DATABASE_URL`: `compose.yaml` tự tạo nó từ `POSTGRES_PASSWORD`.

> ⚠️ **Cảnh báo:**
> - Dùng **API key khác** với key trên máy bạn, và bật giới hạn chi tiêu cho key này.
> - `POSTGRES_PASSWORD` chỉ có tác dụng **lần đầu** database được tạo. Hãy đặt đúng ngay từ bây giờ.
> - Ta dùng `openssl rand -hex` (chỉ gồm chữ số và chữ a–f) để mật khẩu không chứa ký tự đặc biệt như `@`, `/`, vốn làm hỏng định dạng `DATABASE_URL`.

Chỉ cho chủ sở hữu đọc file:

```bash
chmod 600 .env
```

#### Bước 11: Khởi động hệ thống

```bash
docker compose up -d --build
```

Lần đầu mất vài phút. Kiểm tra:

```bash
docker compose ps
```

Đợi `app` và `db` đều `healthy`. Database mới tạo nên đã tự chạy hết các file trong `db/init/` (bảng, dữ liệu mẫu, RAG, hội thoại). Xây chỉ mục RAG:

```bash
docker compose run --rm app python scripts/build_index.py
```

Kiểm tra app trả lời được từ **bên trong** máy chủ:

```bash
curl http://127.0.0.1:8080/health
```

> 💡 Dữ liệu sản phẩm và cửa hàng hiện là dữ liệu mẫu từ `02_seed.sql`. Khi chạy thật, bạn cần nhập dữ liệu thật của cửa hàng và bỏ file seed mẫu.

#### Bước 12: Cài và cấu hình Nginx

```bash
sudo apt install -y nginx
```

Copy cấu hình từ repository:

```bash
sudo cp deploy/nginx/agent.conf /etc/nginx/sites-available/agent
```

Sửa tên miền:

```bash
sudo sed -i 's/cskh.example.com/cskh.<ten-mien-cua-ban>/' /etc/nginx/sites-available/agent
```

Bật cấu hình mới, tắt trang mặc định:

```bash
sudo ln -s /etc/nginx/sites-available/agent /etc/nginx/sites-enabled/agent
```

```bash
sudo rm /etc/nginx/sites-enabled/default
```

Kiểm tra cú pháp và nạp lại:

```bash
sudo nginx -t
```

```bash
sudo systemctl reload nginx
```

Mở cổng web trên firewall:

```bash
sudo ufw allow 'Nginx Full'
```

Trên **máy bạn**, mở trình duyệt vào `http://cskh.<ten-mien-cua-ban>`. Trang chat hiện ra! Thử chat một câu.

#### Bước 13: Bật HTTPS

```bash
sudo apt install -y certbot python3-certbot-nginx
```

```bash
sudo certbot --nginx -d cskh.<ten-mien-cua-ban>
```

Certbot hỏi email (để báo khi chứng chỉ sắp hết hạn) và yêu cầu đồng ý điều khoản. Certbot sẽ tự lấy chứng chỉ, sửa cấu hình Nginx để bật HTTPS và **tự chuyển HTTP sang HTTPS**.

Kiểm tra tự động gia hạn:

```bash
sudo certbot renew --dry-run
```

Mở `https://cskh.<ten-mien-cua-ban>`: thanh địa chỉ có biểu tượng ổ khóa. 🎉

#### Bước 14: Kiểm tra từ Internet

Trên **máy bạn**:

```bash
curl https://cskh.<ten-mien-cua-ban>/health
```

```bash
curl -i https://cskh.<ten-mien-cua-ban>/metrics
```

Lệnh thứ hai phải trả `404`. Thử rate limit (gửi 8 tin liên tục):

```bash
for i in $(seq 1 8); do curl -s -o /dev/null -w "%{http_code} " -X POST https://cskh.<ten-mien-cua-ban>/chat -H "Content-Type: application/json" -d '{"session_id":"test-rl","message":"xin chào"}'; done; echo
```

Kết quả: vài mã `200`, sau đó là `429`.

Kiểm tra database **không** mở ra Internet:

```bash
nc -zv -w 3 <IP> 5432
```

Phải báo lỗi hoặc timeout (không kết nối được). Nếu máy chưa có `nc`, cài bằng `sudo apt install netcat-openbsd`.

#### Bước 15: Xem Grafana an toàn qua SSH tunnel

Grafana chỉ nghe ở `127.0.0.1` của máy chủ. Để xem từ máy bạn, tạo **đường hầm SSH**:

```bash
ssh -L 3000:127.0.0.1:3000 deploy@<IP>
```

Giữ phiên này mở, rồi trên máy bạn vào **http://localhost:3000**. Mọi dữ liệu đi qua kết nối SSH đã mã hóa. Đăng nhập `admin` với `GRAFANA_PASSWORD`, rồi làm lại phần kết nối Prometheus và dashboard như Bài 13 (hoặc import file JSON dashboard nếu bạn đã xuất).

Tương tự, xem API quản trị:

```bash
curl https://cskh.<ten-mien-cua-ban>/admin/handoffs -H "X-API-Key: <ADMIN_API_KEY>"
```

### Phần D: Sao lưu

#### Bước 16: Sao lưu tự động mỗi ngày

Chạy thử một lần:

```bash
~/project_agent/deploy/backup.sh
```

```bash
ls -lh ~/backups/
```

Đặt lịch chạy lúc 2 giờ sáng mỗi ngày:

```bash
crontab -e
```

Chọn trình soạn thảo `nano` nếu được hỏi, thêm dòng sau vào cuối file:

```
0 2 * * * /home/deploy/project_agent/deploy/backup.sh >> /home/deploy/backup.log 2>&1
```

Ý nghĩa: phút `0`, giờ `2`, mọi ngày, mọi tháng, mọi thứ trong tuần. `>> ... 2>&1` ghi cả kết quả và lỗi vào file log. Dán lịch vào [crontab.guru](https://crontab.guru/) để kiểm tra.

#### Bước 17: Thử khôi phục

**Bản sao lưu chưa từng thử khôi phục thì coi như không có.** Thử khôi phục vào một database tạm:

```bash
cd ~/project_agent
```

```bash
docker compose exec -T db createdb -U agent khoi_phuc_thu
```

```bash
gunzip -c ~/backups/agent-$(date +%F).sql.gz | docker compose exec -T db psql -q -U agent -d khoi_phuc_thu
```

```bash
docker compose exec db psql -U agent -d khoi_phuc_thu -c "SELECT count(*) FROM products;"
```

Ra `10` là khôi phục thành công. Xóa database tạm:

```bash
docker compose exec -T db dropdb -U agent khoi_phuc_thu
```

> ⚠️ **Cảnh báo:** bản sao lưu đang nằm **trên chính máy chủ**. Máy chủ hỏng hoặc bị xóa thì mất luôn cả bản sao lưu. Hãy copy định kỳ ra nơi khác: máy bạn (`scp deploy@<IP>:~/backups/*.gz .`), Google Drive hoặc kho lưu trữ S3 (công cụ [rclone](https://rclone.org/)). Nhiều nhà cung cấp VPS cũng có tính năng chụp ảnh (snapshot) cả máy theo lịch.

### Phần E: Tự động deploy (CD)

#### Bước 18: Tạo SSH key riêng cho GitHub Actions

Trên **máy bạn**:

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -N "" -f ~/.ssh/github_actions_deploy
```

Đưa khóa **công khai** lên máy chủ:

```bash
ssh-copy-id -i ~/.ssh/github_actions_deploy.pub deploy@<IP>
```

Trên GitHub: repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**. Tạo 3 secret:

| Tên | Giá trị |
|---|---|
| `VPS_HOST` | `<IP>` |
| `VPS_USER` | `deploy` |
| `VPS_SSH_KEY` | Toàn bộ nội dung file **bí mật** `~/.ssh/github_actions_deploy` (lấy bằng `cat ~/.ssh/github_actions_deploy`), kể cả dòng `-----BEGIN` và `-----END` |

Sau khi lưu secret, có thể xóa file khóa bí mật này khỏi máy bạn, vì nó chỉ dùng cho GitHub Actions.

#### Bước 19: Thêm job deploy

Trên máy bạn, tạo nhánh mới, rồi thêm vào **cuối** `.github/workflows/ci.yml` (job `deploy` thụt lề cùng cấp với `test:`):

```yaml
  deploy:
    needs: test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    concurrency: deploy
    steps:
      - name: Deploy lên VPS qua SSH
        uses: appleboy/ssh-action@v1.2.0
        with:
          host: ${{ secrets.VPS_HOST }}
          username: ${{ secrets.VPS_USER }}
          key: ${{ secrets.VPS_SSH_KEY }}
          script: |
            set -e
            cd ~/project_agent
            git pull --ff-only
            docker compose up -d --build
            docker image prune -f
```

Giải thích:

- **`needs: test`**: chỉ chạy khi job `test` đạt. Code hỏng không bao giờ lên máy chủ.
- **`if: ... push ... main`**: chỉ deploy khi code vào `main`, không deploy khi mới mở PR.
- **`concurrency: deploy`**: hai lần merge sát nhau thì không chạy hai lần deploy chồng lên nhau.
- **`script`**: các lệnh chạy trên máy chủ: kéo code mới, build lại, khởi động lại container thay đổi, dọn image cũ. `git pull --ff-only` từ chối nếu code trên máy chủ bị sửa tay (khác với GitHub). Đây là điều tốt: mọi thay đổi phải đi qua Git.

Commit, push, tạo PR, đợi CI xanh, rồi **Merge**. Vào tab **Actions** xem job `deploy` chạy. Từ giờ, **mỗi lần merge vào `main` là tự động deploy**.

#### Bước 20: Khi bản mới bị lỗi (rollback)

Nếu bản vừa deploy có vấn đề, cách an toàn nhất là **revert** (đảo ngược) commit gây lỗi. Trên máy bạn:

```bash
git switch main && git pull
```

```bash
git log --oneline -5
```

Tìm mã commit gây lỗi, rồi:

```bash
git switch -c revert-loi
```

```bash
git revert <ma-commit>
```

```bash
git push -u origin revert-loi
```

Tạo PR và merge. CD tự deploy lại bản trước đó. Trên GitHub, trang của mỗi PR đã merge cũng có sẵn nút **Revert**.

---

## Kiểm tra kết quả

- [ ] `https://cskh.<ten-mien-cua-ban>` có ổ khóa HTTPS và chat được.
- [ ] `/metrics` trả 404 từ Internet; gửi nhanh nhiều tin bị 429.
- [ ] Không SSH được bằng `root` hay bằng mật khẩu.
- [ ] `sudo ufw status` chỉ mở OpenSSH và Nginx Full.
- [ ] Cổng 5432 không truy cập được từ Internet.
- [ ] Có file sao lưu trong `~/backups/` và đã thử khôi phục thành công.
- [ ] Merge vào `main` thì tự động deploy.
- [ ] Đã rà soát **Checklist bảo mật** ở Bài 12.

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `Permission denied (publickey)` khi SSH | Sai user, hoặc chưa copy key cho user đó | Kiểm tra lại Bước 4. Nếu bị khóa, vào Web Console của nhà cung cấp |
| Tên miền không vào được | DNS chưa cập nhật, hoặc firewall chưa mở 80/443 | `nslookup` kiểm tra IP; `sudo ufw status` |
| `502 Bad Gateway` | Nginx chạy nhưng app chưa chạy | `docker compose ps`, `docker compose logs app` |
| `504 Gateway Timeout` | Agent xử lý quá `proxy_read_timeout` | Xem metric LLM chậm; tăng timeout nếu cần |
| Certbot báo lỗi `Challenge failed` | DNS chưa trỏ đúng, hoặc cổng 80 bị chặn | Đợi DNS cập nhật; `sudo ufw allow 'Nginx Full'` |
| `password authentication failed` sau khi đổi `POSTGRES_PASSWORD` | Mật khẩu chỉ áp dụng lần đầu khởi tạo | Đổi mật khẩu trong database: `ALTER USER agent PASSWORD '...'` qua psql |
| Job deploy báo `ssh: handshake failed` | Secret `VPS_SSH_KEY` thiếu dòng đầu/cuối, hoặc chưa thêm public key lên máy chủ | Dán lại toàn bộ khóa; kiểm tra `~/.ssh/authorized_keys` trên máy chủ |
| `git pull --ff-only` thất bại khi deploy | Có người sửa file trực tiếp trên máy chủ | SSH vào xem `git status`, hoàn tác thay đổi tay |
| Backup cron không chạy | Script chưa có quyền chạy, hoặc sai đường dẫn | `chmod +x deploy/backup.sh`; xem `~/backup.log` |

## Bài tập

1. Cài [UptimeRobot](https://uptimerobot.com/) (miễn phí) giám sát `https://cskh.<ten-mien>/health` mỗi 5 phút, gửi email khi sập. Thử tắt app (`docker compose stop app`) để nhận cảnh báo.
2. Dùng rclone tự động copy bản sao lưu lên Google Drive mỗi ngày (thêm vào cuối `backup.sh`).
3. Kiểm tra chứng chỉ HTTPS của bạn trên [SSL Labs](https://www.ssllabs.com/ssltest/). Bạn được điểm gì?
4. Cài [fail2ban](https://github.com/fail2ban/fail2ban) để tự chặn IP dò mật khẩu SSH. Xem log `sudo journalctl -u ssh` để thấy bot dò tìm máy chủ của bạn liên tục ra sao.
5. Viết file `deploy/HUONG_DAN_VAN_HANH.md` ghi lại: cách deploy, cách rollback, cách khôi phục backup, cách xem log. Đây là tài liệu "runbook" cho chính bạn sau này.

## Checklist hoàn thành

- [ ] VPS đã gia cố: user riêng, SSH key, không root, firewall, tự vá bảo mật
- [ ] Tên miền, Nginx, HTTPS, rate limit hoạt động
- [ ] Bí mật production riêng, `.env` quyền 600
- [ ] Sao lưu tự động hằng ngày, đã thử khôi phục, có bản sao ngoài máy chủ
- [ ] CD tự động deploy khi merge vào `main`, biết cách rollback

🎉 **Chúc mừng! Agent của bạn đã chạy thật trên Internet.** Phần cuối sẽ đưa bạn đi sâu hơn: tự chạy LLM trên GPU và đo hiệu năng.

➡️ Tiếp theo: [Bài 16: Tự chạy LLM bằng vLLM trên GPU](bai-16-self-host-vllm.md)
