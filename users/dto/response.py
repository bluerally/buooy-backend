from users.dtos import LoginResponseData


class AccessTokenResponse(LoginResponseData):
    is_new_user: bool
