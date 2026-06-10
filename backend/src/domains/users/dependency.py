from src.domains.users.serivce import UserService


def get_user_service() -> UserService:
    return UserService()
