import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ldap_config.json")

DEFAULT_CONFIG = {
    "ldap_enabled": False,
    "ldap_host": "",
    "ldap_port": "389",
    "ldap_domain": "",
    "ldap_base_dn": "",
    "ldap_bind_dn": "",
    "ldap_bind_password": "",
    "ldap_user_filter": "(sAMAccountName={username})",
    "ldap_use_ssl": False,
}


def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    return DEFAULT_CONFIG.copy()


def save_config(data: dict):
    with open(CONFIG_PATH, "w") as f:
        json.dump(data, f, indent=2)


def ldap_login(username: str, password: str, config: dict) -> tuple[bool, str]:
    try:
        from ldap3 import Server, Connection, ALL, SUBTREE
        from ldap3.core.exceptions import LDAPException

        port = int(config.get("ldap_port", 389))
        use_ssl = config.get("ldap_use_ssl", False)

        server = Server(config["ldap_host"], port=port, use_ssl=use_ssl, get_info=ALL)

        domain = config.get("ldap_domain", "")
        user_dn = f"{username}@{domain}" if domain else username

        conn = Connection(server, user=user_dn, password=password, auto_bind=True)

        # busca o usuário no AD
        base_dn = config.get("ldap_base_dn", "")
        user_filter = config.get("ldap_user_filter", "(sAMAccountName={username})")
        user_filter = user_filter.replace("{username}", username)

        conn.search(base_dn, user_filter, search_scope=SUBTREE, attributes=["cn"])

        if conn.entries:
            conn.unbind()
            return True, ""

        conn.unbind()
        return False, "Usuário não encontrado no AD."

    except Exception as e:
        return False, f"Erro LDAP: {str(e)}"


def test_ldap_connection(config: dict) -> tuple[bool, str]:
    try:
        from ldap3 import Server, Connection, ALL

        port = int(config.get("ldap_port", 389))
        use_ssl = config.get("ldap_use_ssl", False)
        server = Server(config["ldap_host"], port=port, use_ssl=use_ssl, get_info=ALL)

        bind_dn = config.get("ldap_bind_dn", "")
        bind_pw = config.get("ldap_bind_password", "")

        conn = Connection(server, user=bind_dn, password=bind_pw, auto_bind=True)
        conn.unbind()
        return True, "Conexão bem-sucedida!"
    except Exception as e:
        return False, f"Falha: {str(e)}"
