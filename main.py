from bot import ZonkHandler

if __name__ == '__main__':
    TOKEN_FILE_NAME = "auth_token.txt"

    try:
        token_file = open(TOKEN_FILE_NAME, "r")
        token = token_file.read()
        print(token)
    except FileNotFoundError as error:
        print(f"Unable to locate '{TOKEN_FILE_NAME}', exiting.")
        exit(1)

    ZonkHandler.execute(token)
