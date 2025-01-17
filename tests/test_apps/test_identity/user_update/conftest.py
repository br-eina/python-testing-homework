import pytest

from tests.plugins.identity.user_update import (
    UserUpdateData,
    UserUpdateDataFactory,
)

USER_UPDATE_REQUIRED_FIELD = (
    'first_name',
    'last_name',
    'address',
    'job_title',
    'phone',
)


@pytest.fixture()
def user_update_data(
    user_update_data_factory: UserUpdateDataFactory,
) -> UserUpdateData:
    """User update data with all required fields."""
    return user_update_data_factory()


@pytest.fixture(params=USER_UPDATE_REQUIRED_FIELD)
def user_update_data_without_req_field(
    user_update_data_factory: UserUpdateDataFactory,
    request: pytest.FixtureRequest,
) -> UserUpdateData:
    """Parametrized user update data with 1 missing required field."""
    field = request.param
    return user_update_data_factory(**{field: ''})
