from scripts.seed_required import DEFAULT_DB_NAME, _database_name, _load_json


def test_database_name_lay_tu_path():
    assert _database_name("mongodb://localhost:27017/fuurin") == "fuurin"
    assert _database_name("mongodb+srv://u:p@host.mongodb.net/fuurin?retryWrites=true") == "fuurin"


def test_database_name_trong_thi_dung_mac_dinh():
    assert _database_name("mongodb+srv://u:p@host.mongodb.net/") == DEFAULT_DB_NAME


def test_file_seed_co_roles_va_website():
    roles = _load_json("roles.json")
    names = {row["name"] for row in roles}
    assert names == {"user", "admin"}
    webs = _load_json("social_app.webs.json")
    assert webs[0]["website_name"] == "Fuurin"
