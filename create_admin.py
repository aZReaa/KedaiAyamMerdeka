import argparse
import getpass

from database import db


def main():
    parser = argparse.ArgumentParser(description="Buat atau reset akun admin lokal.")
    parser.add_argument("--username", required=True, help="Username admin")
    parser.add_argument("--password", help="Password admin. Jika kosong, akan diminta lewat prompt.")
    parser.add_argument("--name", default=None, help="Nama admin yang ditampilkan")
    args = parser.parse_args()

    password = args.password or getpass.getpass("Masukkan password admin baru: ").strip()
    if not password:
        raise SystemExit("Password tidak boleh kosong.")

    db.connect()
    result = db.create_or_update_admin(args.username, password, args.name)

    if not result.get("success"):
        raise SystemExit("Gagal membuat atau memperbarui admin.")

    action = result.get("action")
    print(f"Akun admin {args.username!r} berhasil {action}.")


if __name__ == "__main__":
    main()
