from fastapi import APIRouter

router = APIRouter(tags=["Users"])


# @router.get("/users/me", response_model=...)
# async def get_me(
#     payload: ...,
#     uc: ...
# ) -> ...:
#     ...


# @router.patch("/users/me", response_model=...)
# async def update_me(
#     payload: ...,
#     uc: ...
# ) -> ...:
#     ...


# @router.post("/users/me", response_model=...)
# async def delete_me(
#     payload: ...,
#     uc: ...
# ) -> ...:
#     ...


# @router.get("/users/{user-id}", response_model=...)
# async def get_user(
#     payload: ...,
#     uc: ...
# ) -> ...:
#     ...


# @router.patch("/users/{user-id}", response_model=...)
# async def update_user(
#     payload: ...,
#     uc: ...
# ) -> ...:
#     ...


# @router.post("/users/{user-id}", response_model=...)
# async def delete_user(
#     payload: ...,
#     uc: ...
# ) -> ...:
#     ...
