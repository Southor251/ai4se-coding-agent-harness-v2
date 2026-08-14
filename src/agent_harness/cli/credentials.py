from getpass import getpass

from agent_harness.credentials.manager import CredentialManager


def add_credentials_parser(subparsers):
    parser = subparsers.add_parser("credentials", help="manage API credentials")
    credential_subparsers = parser.add_subparsers(dest="credential_command")

    show = credential_subparsers.add_parser("show", help="show credential status")
    show.set_defaults(handler=_show)

    update = credential_subparsers.add_parser("update", help="update credential through hidden input")
    update.set_defaults(handler=_update)

    clear = credential_subparsers.add_parser("clear", help="clear credential after confirmation")
    clear.add_argument("--yes", action="store_true", help="confirm credential removal")
    clear.set_defaults(handler=_clear)


def _show(args) -> int:
    print(CredentialManager().show_status())
    return 0


def _update(args) -> int:
    secret = getpass("API key (input hidden): ").strip()
    if not secret:
        print("cancelled: empty credential")
        return 1
    CredentialManager().update(secret)
    print("configured")
    return 0


def _clear(args) -> int:
    confirmed = args.yes or input("Clear the stored API key? [y/N]: ").strip().lower() in {"y", "yes"}
    if not confirmed:
        print("cancelled")
        return 0
    CredentialManager().clear()
    print("not configured")
    return 0