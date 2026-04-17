# Potter Ubuntu Deploy

This setup runs both services on the same Ubuntu server:

- FastAPI backend on `127.0.0.1:8000`
- Next.js frontend on `127.0.0.1:3000`
- Nginx on port `80` forwarding `/api` to backend and everything else to frontend

## 1. Server Prep

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nodejs npm nginx git
sudo useradd -m -s /bin/bash potter || true
sudo mkdir -p /opt/potter-profits
sudo chown -R potter:potter /opt/potter-profits
```

## 2. Copy Project

```bash
cd /opt
sudo git clone <your-repo-url> potter-profits
sudo chown -R potter:potter /opt/potter-profits
```

## 3. Backend Setup

```bash
cd /opt/potter-profits/backend
python3 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env`:

- `LOCAL_DATABASE_URL=sqlite:////opt/potter-profits/backend/potter_local.db`
- `DATABASE_URL=...` your Supabase pooler URL
- `REMOTE_DATABASE_URL=...` same Supabase pooler URL
- `ENABLE_SCHEDULER=true`
- `ENABLE_REMOTE_SYNC=true`

## 4. Frontend Setup

```bash
cd /opt/potter-profits/frontend
npm install
cp /opt/potter-profits/deploy/frontend.production.env.example .env.production
npm run build
```

## 5. systemd Services

```bash
sudo cp /opt/potter-profits/deploy/potter-backend.service /etc/systemd/system/
sudo cp /opt/potter-profits/deploy/potter-frontend.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable potter-backend potter-frontend
sudo systemctl start potter-backend potter-frontend
```

## 6. Nginx

```bash
sudo cp /opt/potter-profits/deploy/potter-nginx.conf /etc/nginx/sites-available/potter
sudo ln -sf /etc/nginx/sites-available/potter /etc/nginx/sites-enabled/potter
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

## 7. Verify

```bash
systemctl status potter-backend
systemctl status potter-frontend
curl http://127.0.0.1:8000/health
curl http://127.0.0.1/
```

## Notes

- Use the server's public IPv4 address in your browser, not its private VPC IP.
- The private IP is useful only for internal networking inside your cloud account.
- For HTTPS later, add a domain and use Certbot with Nginx.
