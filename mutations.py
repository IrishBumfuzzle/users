import os

import strawberry
from fastapi.encoders import jsonable_encoder

from db import db
from models import User

# import all models and types
from otypes import Info, PhoneInput, RoleInput, UserDataInput

inter_communication_secret = os.getenv("INTER_COMMUNICATION_SECRET")


# update role of user with uid
@strawberry.mutation
def updateRole(roleInput: RoleInput, info: Info) -> bool:
    user = info.context.user
    if not user:
        raise Exception("Not logged in!")

    roleInputData = jsonable_encoder(roleInput)

    # check if user is admin
    if user.get("role", None) not in ["cc"]:
        raise Exception("Authentication Error! Only admins can assign roles!")

    # check if the secret is correct
    if (
        roleInputData.get("inter_communication_secret", None)
        != inter_communication_secret
    ):
        raise Exception("Authentication Error! Invalid secret!")

    db_user = db.users.find_one({"uid": roleInputData["uid"]})

    # insert if not exists
    if not db_user:
        new_user = User(uid=roleInputData["uid"])
        db.users.insert_one(jsonable_encoder(new_user))

    # update role in database
    db.users.update_one(
        {"uid": roleInputData["uid"]},
        {"$set": {"role": roleInputData["role"]}},
    )

    return True


@strawberry.mutation
def updateUserPhone(userDataInput: PhoneInput, info: Info) -> bool:
    user = info.context.user
    if not user:
        raise Exception("Not logged in!")

    userData = jsonable_encoder(userDataInput)

    # Validate the data by putting in the model
    try:
        User(**userData)
    except Exception:
        raise Exception("Invalid phone number!")

    # check if user has access
    if not (
        user.get("role", None) in ["cc", "club"]
        or user.get("uid", None) == userData["uid"]
    ):
        raise Exception("You are not allowed to perform this action!")

    db.users.update_one(
        {"uid": userData["uid"]},
        {"$set": {"phone": userData["phone"]}},
    )

    return True


@strawberry.mutation
def updateUserData(userDataInput: UserDataInput, info: Info) -> bool:
    user = info.context.user
    if not user:
        raise Exception("Not logged in!")

    userData = jsonable_encoder(userDataInput)

    # check if user has access
    if (
        user.get("role", None) not in ["cc"]
        and user.get("uid", None) != userData["uid"]
    ):
        raise Exception("You are not allowed to perform this action!")

    # Validate the data by putting in the model
    User(**userData)

    db.users.update_one(
        {"uid": userData["uid"]},
        {"$set": {"img": userData["img"], "phone": userData["phone"]}},
    )

    return True


# register all mutations
mutations = [
    updateRole,
    updateUserPhone,
    updateUserData,
]
