# IoTp���WebLb

��FastAPI + Vue.js�IoTpn����WebѧLbЛ��pnѧ��Mn�I��

## �߶�

```
                                                           
   Vue.jsM�           FastAPI�          �	p���   
   ((7Lb)    �  �   (API�)     �  �   (��)     
                                                           
                                                      
                                                      
        �                       �                       �
                                                           
   WebSocket            InfluxDB             InfluxDB      
   (���)           (��pn)            (��pn)     
                                                           
```

## �/

### �
- **FastAPI**: �'�Python WebF�
- **SQLite**: �߶X�
- **InfluxDB**: ��pnX�
- **WebSocket**: ���
- **Docker**: �h�r

### M�
- **Vue.js 3**: ��M�F�
- **Element Plus**: UI���
- **ECharts**: pn��
- **Vite**: ���w
- **Vuex**: ��

## ��y'

### =' �ѧ
- ����ѧ
- �/�/\b/�/�6
- �D�(ŵ
- ����

### =� pnѧ
- ��pnU:
- ��pn��
- pnߡ�
- pn����

### � Mn�
- ExcelMn��
 
- Mn����
- Mn�Ԍ�(
- Mn��

### =� ��ѧ
- ��D�ѧ
- ����
- ���ס
- e���

## � �

### ���B
- Docker >= 20.10
- Docker Compose >= 2.0
- Node.js >= 16.0 ( ѯ�)
- Python >= 3.11 ( ѯ�)

### 1. ��Mn
```bash
# 6����Mn��
cp .env.example .env

# �����
vi .env
```

### 2. /��
```bash
# /�@	�
docker-compose up -d

# ���
docker-compose ps
```

### 3. ����
- M�Lb: http://localhost:3000
- �API: http://localhost:8000
- API�c: http://localhost:8000/docs
- InfluxDB: http://localhost:8086

## y�ӄ

```
edge_iot/
   api/                        # FastAPI�
      main.py                # �(e�
      routers/               # API�1
         processes.py       # ��API
         data.py           # pn��API
         config.py         # Mn�API
         system.py         # ��ѧAPI
         websocket.py      # WebSocket�
      services/             # �;��
      models/               # pn!�
      core/                 # 8ß�
      tests/                # K��
   frontend/                  # Vue.jsM�
      src/
         main.js           # �(e�
         App.vue           # 9��
         router/           # �1Mn
         store/            # ��
         components/       # lq��
         views/            # ub��
         services/         # API�
         utils/            # �w�p
      tests/                # K��
   nginx/                     # NginxMn
   docker-compose.yml         # Docker���
   .env.example              # ����!
   README.md                 # y�c
```

##  �W

### � �

#### /� ѯ�
```bash
# �e��U
cd api

# �ŝV
pip install -r requirements.txt

# /� ��h
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### �LK�
```bash
# �L@	K�
pytest

# �LUCK�
pytest -m unit

# �և�J
pytest --cov --cov-report=html
```

### M� �

#### /� ѯ�
```bash
# �eM��U
cd frontend

# �ŝV
npm install

# /� ��h
npm run dev
```

#### �LK�
```bash
# �LUCK�
npm run test

# �LK�v�և�J
npm run test:coverage

# �LE2EK�
npm run test:e2e
```

## �rW

### ����r

1. **��M�(**
   ```bash
   cd frontend
   npm run build
   ```

2. **/���**
   ```bash
   docker-compose --profile production up -d
   ```

3. **MnSSL�f**
   ```bash
   # SSL�f>n(nginx/ssl/�U
   cp your-cert.pem nginx/ssl/
   cp your-key.pem nginx/ssl/
   ```

## ��y'

### ���
- WebSocket��pn�
- ������
- �߶��ѧ

### pn��
- ECharts�hU:
- ��pn���
- ���
- ��D�(�

### ͔��
- MOU:�
- ����}Lb
- �(7S�

### ��('
- �h�r
- ���/
- pnEX�
- e���:6

## API��

### ��
```
GET    /api/processes              # ��@	��
POST   /api/processes/start        # /��
POST   /api/processes/stop         # \b�
POST   /api/processes/restart      # �/�
GET    /api/processes/{pid}/logs   # �����
```

### pn��
```
GET    /api/data/realtime         # �֞�pn
GET    /api/data/history          # �ֆ�pn
GET    /api/data/statistics       # ��pnߡ
GET    /api/data/devices          # �־h
```

### Mn�
```
POST   /api/config/upload         # 
 ExcelMn
GET    /api/config/current        # ��SMMn
POST   /api/config/apply          # �(�Mn
GET    /api/config/validate       # ��Mn��
```

### ��ѧ
```
GET    /api/system/status         # ���߶
GET    /api/system/health         # e���
GET    /api/system/metrics        # ����
```

## /

�	�������T�
- GitHub Issues
- ��: support@example.com