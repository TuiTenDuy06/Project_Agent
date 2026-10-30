from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from agent.config import settings

# open=False: chỉ mở kết nối khi app khởi động (hoặc khi script gọi pool.open()).
pool = ConnectionPool(
    settings.database_url,
    min_size=1,
    max_size=10,
    kwargs={"row_factory": dict_row},
    open=False,
)
