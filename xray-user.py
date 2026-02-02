#!/usr/bin/env python3

XRAY_CONFIG_F="/usr/local/etc/xray/config.json"
XRAY_KEYS_F="/usr/local/etc/xray/.keys"
XRAY_USERS_F="/usr/local/etc/xray/.users.json"

import sys
import json
import argparse
import subprocess
import socket
from contextlib import suppress


def write_json(filepath, data):
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)

def get_xrayconfig() -> dict:
    with open(XRAY_CONFIG_F, "r") as f:
        xrayconfig = json.load(f)
    return xrayconfig


class Inbound:
    """Class for inbound info"""

    def __init__(self, protocol: str,
                       port: int, 
                       network: str,
                       snis: list[str],
                       clients: list[dict[str, str]], 
                       shortids: list[str]):
        self.protocol = protocol
        self.port = port
        self.network = network
        self.snis = snis
        self.clients = clients
        self.shortids = shortids
        if self.protocol == "vless":
            assert len(self.clients) == len(self.shortids), \
            "Incorrect Xray 'inbounds' config: number of 'clients' must be the same as number or 'shortIds'"
        else:
            raise ValueError(f"Inbound protocol '{self.protocol}' is not supported")

    def get_sharelinks(self) -> dict[str, str]:
        """
        Returs sharelinks in format {username: sharelink}
        """
        ip = subprocess.run(["curl", "-s", "icanhazip.com"], check=True, capture_output=True).stdout.decode().rstrip()
        with open(XRAY_KEYS_F) as f:
            pbk = _parse_x25519(f.read())["publicKey"]
        hostname = socket.gethostname()

        sharelinks = dict()
        for i, client in enumerate(self.clients):
            sharelink = f"{self.protocol}://{client['uuid']}@{ip}:{self.port}?security=reality&"
            if self.protocol == "vless":
                # TODO: spx probably may be deleted
                # TODO: only first sni is used
                common = f"sni={self.snis[0]}&fp=firefox&pbk={pbk}&sid={self.shortids[i]}&spx=/&"
                if self.network == "tcp":
                    sharelink += f"{common}type=tcp&flow=xtls-rprx-vision&encryption=none"
                elif self.network == "xhttp":
                    sharelink += f"path=%2F&host=&mode=auto&{common}type=xhttp&encryption=none"
                else:
                    raise ValueError(f"Inbound network '{self.network}' is not supported")
                sharelinks[client["email"]] = sharelink + f" #{hostname} {self.protocol}-{self.network}"
        return sharelinks


def get_inbounds_info(xrayconfig) -> list[Inbound]:
    inbounds = []
    for inbound in xrayconfig["inbounds"]:
        inbounds.append(Inbound(
            inbound["protocol"],
            inbound["port"],
            inbound["streamSettings"]["network"],
            inbound["streamSettings"].get("realitySettings", {}).get("serverNames", []),
            inbound["settings"]["clients"],
            inbound["streamSettings"].get("realitySettings", {}).get("shortIds", [])
        ))
    return inbounds
    
def get_all_clientnames(inbounds: list[Inbound]) -> set[str]:
    clients = set()
    for inbound in inbounds:
        for clientconf in inbound.clients:
            clients.add(clientconf["email"])
    return clients

def get_all_users() -> dict[str, dict[str, str]]:
    users = dict()
    with suppress(FileNotFoundError), open(XRAY_USERS_F, "r") as f:
        users = json.load(f)
    return users

def show_users():
    clients = get_all_clientnames(get_inbounds_info(get_xrayconfig()))
    users = get_all_users()
    print(f"Active clients: {', '.join(clients)}")
    inactive_users = set(users) - clients
    print(f"Inactive users: {', '.join(inactive_users)}")
    missing_users = clients - set(users)
    if missing_users:
        sys.stderr.write(f"ERROR: Following users missing in {XRAY_USERS_F}: {', '.join(missing_users)}\n")
        sys.exit(4)

def generate_user() -> dict[str, str]:
    user = dict()
    res = subprocess.run(["xray", "uuid"], check=True, capture_output=True)
    user["uuid"] = res.stdout.decode().rstrip()
    assert len(user["uuid"]) == 36
    res = subprocess.run(["openssl", "rand", "-hex", "8"], check=True, capture_output=True)
    user["shortId"] = res.stdout.decode().rstrip()
    assert len(user["shortId"]) == 16
    return user

def _parse_x25519(output: str) -> dict[str, str]:
    keys = dict()
    for line in output.splitlines():
        if line.startswith("PrivateKey: "):
            keys["privateKey"] = line[12:]
        elif line.startswith("Password: "):
            keys["publicKey"] = line[10:]
        elif line.startswith("Hash32: "):
            keys["hash32"] = line[8:]
    assert len(keys["privateKey"]) == 43, "incorrect lenght of private key (must be 43)"
    assert len(keys["publicKey"]) == 43, "incorrect lenght of public key (must be 43)"
    assert len(keys["hash32"]) == 43, "incorrect lenght of keys check sum (must be 43)"
    return keys

def add_user(username):
    xrayconfig = get_xrayconfig()

    inbounds = get_inbounds_info(xrayconfig)
    for inbound in inbounds:
        for client in inbound.clients:
            if username == client["email"]:
                sys.stderr.write(f"User '{username}' allready configured\n")
                sys.exit(5)

    users = get_all_users()
    if username not in users:
        print(f"Creating new user '{username}'")
        userinfo = generate_user()
        users[username] = userinfo
        write_json(XRAY_USERS_F, users)
    else:
        print(f"Restoring user '{username}'")
        userinfo = users[username]

    shortid = userinfo.pop("shortId")
    userinfo["email"] = username

    # User is added to all inbounds
    for inbound in inbounds:
        if inbound.protocol == "vless":
            inbound.shortids.append(shortid)
            if inbound.network == "tcp":
                userinfo["flow"] = "xtls-rprx-vision"
            elif inbound.network == "xhttp":
                userinfo["flow"] = ""
            
            inbound.clients.append(userinfo)

    write_json(XRAY_CONFIG_F, xrayconfig)

def rm_user(username: str, force: bool=False):
    xrayconfig = get_xrayconfig()

    user_removed = False
    inbounds = get_inbounds_info(xrayconfig)
    if username:
        for inbound in inbounds:
            for i, client in enumerate(inbound.clients):
                if username == client["email"]:
                    inbound.clients.pop(i)
                    user_removed = True
                    print(f"User '{username}' was removed from inbound")
                    break
            inbound.shortids.pop(i)
    else:
        for inbound in inbounds:
            inbound.clients.clear()
            inbound.shortids.clear()
            user_removed = True
            print("All users were removed from inbound")
    
    if user_removed:
        write_json(XRAY_CONFIG_F, xrayconfig)
    elif not force:
        sys.stderr.write(f"User '{username}' was not found in Xray inbounds config\n")
        sys.exit(3)

    if force:
        users = get_all_users()
        if username:
            if username in users:
                users.pop(username)
                print(f"User '{username}' was removed from database")
            else:
                sys.stderr.write(f"User '{username}' was not found in database\n")
                sys.exit(3)
        else:
            users.clear()
            print("All users were removed from database")

        write_json(XRAY_USERS_F, users)


def show_link(username: str):
    inbounds = get_inbounds_info(get_xrayconfig())
    clients = get_all_clientnames(inbounds)
    if username in clients:
        for inbound in inbounds:
            sharelinks = inbound.get_sharelinks()
            if username in sharelinks:
                print(sharelinks[username])
    else:
        sys.stderr.write(f"User '{username}' was not found in Xray inbounds config\n")
        sys.exit(3)


def main():
    parser = argparse.ArgumentParser()

    group = parser.add_mutually_exclusive_group()
    group.add_argument("-show", action="store_true", help="show configured inbound users")
    group.add_argument("-add", metavar="username", help="add user to inbound")
    group.add_argument('-rm', metavar="username", help="remove user from inbound, but preserve in database")
    group.add_argument("-rm-all", action="store_true", help="remove all users from inbound, but preserve in database")
    group.add_argument('-link', metavar="username", help="show user sharelink, with qr code if possible")

    parser.add_argument("-f", "--force", action="store_true", help="remove from database also")

    args = parser.parse_args()

    if args.show:
        show_users()
    elif args.add:
        add_user(args.add)
    elif args.rm:
        rm_user(args.rm, args.force)
    elif args.rm_all:
        rm_user("", args.force)
    elif args.link:
        show_link(args.link)
    
    else:
        parser.print_help()
        sys.exit(2)

if __name__ == "__main__":
    try:
        main()
    except Exception as ex:
        sys.stderr.write(f"ERROR: {ex}\n")
        sys.exit(1)
