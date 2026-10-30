# Bài 01: Chuẩn bị môi trường làm việc

## Mục tiêu

Sau bài này bạn sẽ:

- Dùng được **terminal** để di chuyển giữa các thư mục và chạy lệnh.
- Cài xong **Git, Python 3.12, VS Code, Docker**.
- Có tài khoản **GitHub**, đẩy (push) được code lên GitHub bằng SSH key.
- Tạo được **môi trường ảo Python** (virtualenv) cho dự án.

## Kiến thức cần học

| Chủ đề | Tài liệu |
|---|---|
| Dòng lệnh Linux cơ bản | [The Linux Command Line (miễn phí)](https://linuxcommand.org/tlcl.php), chương 1–5 |
| Git cơ bản | [Pro Git, tiếng Việt](https://git-scm.com/book/vi/v2), chương 1–3 |
| GitHub | [GitHub Docs: Get started](https://docs.github.com/en/get-started) |
| Môi trường ảo Python | [venv, Python docs](https://docs.python.org/3/library/venv.html) |
| WSL (nếu dùng Windows) | [Cài WSL, Microsoft](https://learn.microsoft.com/vi-vn/windows/wsl/install) |

---

## Phần lý thuyết

### Terminal là gì?

Terminal (còn gọi là dòng lệnh, shell, console) là cửa sổ để bạn **ra lệnh cho máy tính bằng chữ** thay vì bấm chuột. Lập trình viên dùng terminal vì:

- Mọi công cụ (Git, Python, Docker) đều điều khiển bằng lệnh.
- Máy chủ trên Internet (VPS) **không có giao diện đồ họa**, chỉ có terminal.
- Lệnh có thể ghi lại, chia sẻ và tự động hóa.

### Git và GitHub khác nhau thế nào?

- **Git** là phần mềm trên máy bạn. Nó **ghi lại lịch sử thay đổi** của code. Mỗi lần ghi gọi là một **commit**. Nhờ đó bạn quay lại được bất kỳ phiên bản cũ nào.
- **GitHub** là trang web **lưu trữ kho Git (repository) trên mạng**. Nó giúp bạn sao lưu code, làm việc nhóm và chạy tự động (CI/CD ở Bài 14).

### Môi trường ảo (virtualenv) để làm gì?

Mỗi dự án Python cần các thư viện riêng, đôi khi khác phiên bản nhau. Môi trường ảo là **một thư mục chứa Python và thư viện riêng cho từng dự án**. Nhờ vậy các dự án không đụng nhau.

### Docker là gì? (giới thiệu ngắn)

Docker chạy phần mềm trong các **container**, tức là các "hộp" đóng gói sẵn mọi thứ phần mềm cần. Ở Bài 05 bạn dùng Docker để chạy database mà không phải cài phức tạp. Bài 11 sẽ học Docker sâu hơn.

---

## Thực hành từng bước

### Bước 1: Chuẩn bị hệ điều hành

Toàn bộ khóa học dùng lệnh kiểu **Linux**. Máy chủ thật cũng chạy Linux, nên học theo cách này là chuẩn nhất.

**Nếu bạn dùng macOS hoặc Linux:** bạn đã có sẵn terminal. Trên macOS, mở ứng dụng **Terminal** (nhấn `Cmd + Space`, gõ "Terminal").

**Nếu bạn dùng Windows:** cài **WSL2** (Windows Subsystem for Linux), tức là một Linux Ubuntu chạy bên trong Windows.

1. Bấm chuột phải vào nút Start, chọn **Terminal (Admin)** hoặc **PowerShell (Admin)**.
2. Gõ lệnh sau rồi nhấn Enter:

   ```bash
   wsl --install -d Ubuntu-24.04
   ```

3. Khởi động lại máy khi được yêu cầu.
4. Mở ứng dụng **Ubuntu** từ menu Start. Lần đầu nó hỏi tên người dùng (username) và mật khẩu. Hãy đặt và **ghi nhớ mật khẩu** này, vì bạn sẽ cần nó khi chạy lệnh `sudo`.

> ⚠️ **Cảnh báo:** từ giờ trở đi, trên Windows hãy **luôn gõ lệnh trong cửa sổ Ubuntu**, không gõ trong PowerShell. Code dự án cũng để bên trong Ubuntu (thư mục `~`), không để ở `C:\`. Để ở `C:\` sẽ chậm và dễ lỗi quyền truy cập.

### Bước 2: Làm quen với terminal

Gõ thử từng lệnh sau và quan sát kết quả:

```bash
pwd
```

`pwd` (print working directory) cho biết bạn đang đứng ở thư mục nào.

```bash
ls
```

`ls` liệt kê file và thư mục trong thư mục hiện tại.

```bash
mkdir thu-nghiem
```

`mkdir` tạo thư mục mới tên `thu-nghiem`.

```bash
cd thu-nghiem
```

`cd` di chuyển vào thư mục. `cd ..` để lùi ra thư mục cha. `cd ~` để về thư mục nhà (home).

```bash
echo "xin chao" > ghi-chu.txt
```

Lệnh này tạo file `ghi-chu.txt` chứa dòng "xin chao".

```bash
cat ghi-chu.txt
```

`cat` in nội dung file ra màn hình.

```bash
cd .. && rm -r thu-nghiem
```

Lệnh này quay ra ngoài và xóa thư mục thử nghiệm. `&&` nghĩa là "chạy lệnh sau nếu lệnh trước thành công".

> ⚠️ **Cảnh báo:** `rm` xóa **vĩnh viễn**, không qua thùng rác. Luôn kiểm tra kỹ đường dẫn trước khi chạy `rm -r`.

💡 **Mẹo:**

- Nhấn `Tab` để tự hoàn thành tên file hoặc thư mục.
- Nhấn mũi tên `↑` để gọi lại lệnh cũ.
- Nhấn `Ctrl + C` để dừng một lệnh đang chạy.

### Bước 3: Cài Git, Python và công cụ cơ bản

**Ubuntu / WSL:**

```bash
sudo apt update
```

```bash
sudo apt install -y git curl build-essential python3 python3-venv python3-pip
```

`sudo` nghĩa là chạy với quyền quản trị, nên nó sẽ hỏi mật khẩu Ubuntu của bạn. Khi gõ mật khẩu, màn hình **không hiện ký tự nào**, đó là bình thường.

Kiểm tra phiên bản Python:

```bash
python3 --version
```

Bạn cần **Python 3.11 trở lên**. Ubuntu 24.04 có sẵn 3.12. Nếu bản Ubuntu của bạn cũ hơn và chỉ có 3.10, hãy cài thêm [uv](https://docs.astral.sh/uv/) rồi dùng `uv python install 3.12`.

**macOS:** cài [Homebrew](https://brew.sh) trước, rồi chạy:

```bash
brew install git python@3.12
```

### Bước 4: Cài VS Code

1. Tải VS Code tại [code.visualstudio.com](https://code.visualstudio.com/) và cài như phần mềm bình thường.
2. Mở VS Code, vào tab **Extensions** (biểu tượng 4 ô vuông bên trái), cài các extension:
   - **Python** (của Microsoft)
   - **Ruff** (kiểm tra lỗi code Python)
   - **Docker** (của Microsoft)
   - Nếu dùng Windows: **WSL** (của Microsoft)
3. Nếu dùng Windows: trong cửa sổ Ubuntu, khi đứng ở thư mục dự án, gõ `code .` thì VS Code sẽ mở và kết nối thẳng vào Ubuntu.

### Bước 5: Cài Docker

- **Windows và macOS:** cài [Docker Desktop](https://www.docker.com/products/docker-desktop/). Trên Windows, khi cài nhớ chọn **"Use WSL 2 based engine"**. Sau khi cài, vào **Settings → Resources → WSL Integration** và bật cho Ubuntu.
- **Linux:** làm theo [hướng dẫn chính thức](https://docs.docker.com/engine/install/ubuntu/), rồi thêm user vào nhóm docker để khỏi phải gõ `sudo`:

  ```bash
  sudo usermod -aG docker $USER
  ```

  Sau đó đăng xuất và đăng nhập lại.

Kiểm tra:

```bash
docker run --rm hello-world
```

Nếu thấy dòng `Hello from Docker!` là thành công.

### Bước 6: Tạo tài khoản GitHub và cấu hình Git

1. Đăng ký tài khoản tại [github.com](https://github.com).
2. Khai báo tên và email cho Git. Email nên trùng với email GitHub:

   ```bash
   git config --global user.name "<Ten Cua Ban>"
   ```

   ```bash
   git config --global user.email "<email-cua-ban@example.com>"
   ```

   ```bash
   git config --global init.defaultBranch main
   ```

### Bước 7: Tạo SSH key để kết nối GitHub

SSH key là một **cặp khóa**: khóa bí mật (private key) nằm trên máy bạn, khóa công khai (public key) đưa cho GitHub. GitHub dùng nó để nhận ra bạn mà không cần mật khẩu. Bạn cũng sẽ dùng SSH key để đăng nhập VPS ở Bài 15.

1. Tạo khóa:

   ```bash
   ssh-keygen -t ed25519 -C "<email-cua-ban@example.com>"
   ```

   Nhấn Enter để chấp nhận vị trí mặc định. Bạn có thể đặt passphrase (mật khẩu cho khóa) hoặc để trống.

2. In khóa **công khai** ra màn hình:

   ```bash
   cat ~/.ssh/id_ed25519.pub
   ```

3. Copy toàn bộ dòng in ra (bắt đầu bằng `ssh-ed25519`).
4. Trên GitHub: bấm avatar → **Settings** → **SSH and GPG keys** → **New SSH key**. Dán vào ô Key, đặt tên (ví dụ "May ca nhan") rồi bấm **Add SSH key**.
5. Kiểm tra kết nối:

   ```bash
   ssh -T git@github.com
   ```

   Gõ `yes` nếu được hỏi. Thấy `Hi <ten>! You've successfully authenticated` là thành công.

> ⚠️ **Cảnh báo:** file `~/.ssh/id_ed25519` (không có đuôi `.pub`) là **khóa bí mật**. Không bao giờ gửi file này cho ai, không dán lên mạng, không commit vào Git.

### Bước 8: Lấy kho code dự án về máy

Nếu bạn đã có repository `project_agent` trên GitHub, hãy clone về:

```bash
cd ~
```

```bash
git clone git@github.com:<tai-khoan-github>/project_agent.git
```

```bash
cd project_agent
```

Nếu chưa có, vào GitHub bấm **New repository**, đặt tên `project_agent`, chọn **Private**, tích **Add a README file**, bấm **Create repository**. Sau đó clone như trên.

Mở dự án bằng VS Code:

```bash
code .
```

### Bước 9: Tạo file `.gitignore`

`.gitignore` liệt kê những file **Git không được theo dõi**: file rác, thư viện tải về, và quan trọng nhất là file chứa mật khẩu.

Tạo file `.gitignore` ở thư mục gốc dự án:

```gitignore
# Môi trường ảo Python
.venv/

# File sinh ra khi chạy Python
__pycache__/
*.pyc
*.egg-info/
.pytest_cache/
.ruff_cache/

# Bí mật: API key, mật khẩu. KHÔNG BAO GIỜ commit
.env

# Kết quả benchmark (file lớn)
benchmark/results/
```

### Bước 10: Tạo môi trường ảo Python

Đứng ở thư mục `project_agent`, chạy:

```bash
python3 -m venv .venv
```

Lệnh này tạo thư mục `.venv` chứa một bản Python riêng cho dự án.

Kích hoạt môi trường ảo:

```bash
source .venv/bin/activate
```

Đầu dòng lệnh sẽ hiện `(.venv)`. Từ giờ, `python` và `pip` sẽ dùng bản trong `.venv`.

```bash
python --version
```

```bash
pip install --upgrade pip
```

> 💡 **Mẹo:** mỗi lần mở terminal mới để làm dự án, bạn phải chạy lại `source .venv/bin/activate`. Nếu gặp lỗi `ModuleNotFoundError` thì 90% là do quên bước này.

Trong VS Code: nhấn `Ctrl + Shift + P`, gõ **Python: Select Interpreter**, chọn bản có đường dẫn `.venv`.

### Bước 11: Commit đầu tiên

```bash
git status
```

`git status` cho biết file nào mới hoặc đã sửa. Bạn sẽ thấy `.gitignore` màu đỏ (chưa được theo dõi). Thư mục `.venv` **không** xuất hiện, nhờ `.gitignore`.

```bash
git add .gitignore
```

```bash
git commit -m "Thêm .gitignore"
```

```bash
git push
```

Vào trang GitHub của repository, bạn sẽ thấy file `.gitignore` vừa đẩy lên.

🧠 **Hiểu sâu, quy trình Git hằng ngày:**

```
sửa code → git status → git add <file> → git commit -m "mô tả" → git push
```

- `git add` chọn những thay đổi muốn lưu (đưa vào "staging").
- `git commit` lưu một bản chụp vào lịch sử trên máy.
- `git push` đẩy lịch sử lên GitHub.
- `git log --oneline` xem lịch sử commit.
- `git diff` xem chi tiết những gì đã sửa nhưng chưa `add`.

---

## Kiểm tra kết quả

Chạy lần lượt và đảm bảo không có lỗi:

```bash
git --version
```

```bash
python --version
```

```bash
docker --version
```

```bash
ssh -T git@github.com
```

```bash
git log --oneline
```

Lệnh cuối phải hiện commit "Thêm .gitignore".

## Lỗi thường gặp

| Lỗi | Nguyên nhân | Cách sửa |
|---|---|---|
| `Permission denied (publickey)` khi `git push` | GitHub chưa có SSH key của bạn | Làm lại Bước 7, kiểm tra đã dán đúng file `.pub` |
| `docker: permission denied ... docker.sock` | User chưa thuộc nhóm docker (Linux) | Chạy `sudo usermod -aG docker $USER` rồi đăng xuất, đăng nhập lại |
| `Cannot connect to the Docker daemon` | Docker Desktop chưa mở | Mở Docker Desktop, đợi biểu tượng cá voi đứng yên |
| `python: command not found` | Chưa kích hoạt venv, hoặc hệ thống chỉ có `python3` | Chạy `source .venv/bin/activate` |
| `The virtual environment was not created successfully` | Thiếu gói venv | `sudo apt install python3-venv` |

## Bài tập

1. Tạo file `ghi-chu-hoc-tap.md` trong dự án, ghi lại 10 lệnh terminal vừa học và ý nghĩa của chúng. Commit và push.
2. Sửa file đó, chạy `git diff` để xem thay đổi, rồi commit lần nữa. Chạy `git log --oneline` để thấy 2 commit.
3. Đọc chương 2 sách Pro Git và trả lời: `git restore <file>` dùng để làm gì?
4. (Nâng cao) Tạo nhánh mới bằng `git switch -c thu-nghiem`, sửa một file, commit, rồi quay về `main` bằng `git switch main`. File trên `main` có bị đổi không? Tại sao?

## Checklist hoàn thành

- [ ] Mở được terminal (Ubuntu trên Windows) và dùng được `cd`, `ls`, `pwd`, `mkdir`, `cat`
- [ ] `git`, `python3` (≥ 3.11), `docker` đều chạy được
- [ ] `ssh -T git@github.com` báo thành công
- [ ] Đã clone `project_agent` và mở bằng VS Code
- [ ] Có `.gitignore`, có `.venv` và đã kích hoạt
- [ ] Đã push commit đầu tiên lên GitHub

➡️ Tiếp theo: [Bài 02: Kiến thức web cần thiết](bai-02-kien-thuc-web.md)
