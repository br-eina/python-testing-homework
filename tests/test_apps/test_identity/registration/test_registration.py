import json
from http import HTTPStatus

import httpretty
import pytest
from django.test import Client
from django.urls import reverse

from config.settings import SETTINGS
from server.apps.identity.models import User
from tests.plugins.identity.registration import (
    ExternalAPIUserData,
    RegistrationData,
    UserData,
)
from tests.test_apps.conftest import FieldMissingAssertion
from tests.test_apps.test_identity.conftest import UserAssertion
from tests.test_apps.test_identity.registration.conftest import (
    ExternalAPIUserAssertion,
)

URL_PATH = reverse('identity:registration')


@pytest.mark.django_db()
def test_page_renders(client: Client) -> None:
    """Basic `get` method works."""
    response = client.get(path=URL_PATH)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db()
def test_no_password(
    client: Client,
    registration_data_without_password: RegistrationData,
    assert_field_missing: FieldMissingAssertion,
) -> None:
    """Registration fails if password is not provided."""
    response = client.post(
        path=URL_PATH,
        data=registration_data_without_password,
    )
    assert response.status_code == HTTPStatus.OK
    assert_field_missing(response.content)


@pytest.mark.django_db()
def test_no_required_field(
    client: Client,
    registration_data_without_req_field: RegistrationData,
    assert_field_missing: FieldMissingAssertion,
) -> None:
    """Registration fails if any required field is not provided."""
    response = client.post(
        path=URL_PATH,
        data=registration_data_without_req_field,
    )
    assert response.status_code == HTTPStatus.OK
    assert_field_missing(response.content)


@pytest.mark.django_db()
def test_empty_date_of_birth(
    client: Client,
    registration_data_empty_birth_date: RegistrationData,
    user_data_empty_birth_date: UserData,
    assert_correct_user: UserAssertion,
) -> None:
    """Registration is successful if date of birth is empty."""
    response = client.post(
        path=URL_PATH,
        data=registration_data_empty_birth_date,
    )
    assert response.status_code == HTTPStatus.FOUND
    assert_correct_user(
        registration_data_empty_birth_date['email'],
        user_data_empty_birth_date,
    )


@pytest.mark.django_db()
def test_email_format_invalid(
    client: Client,
    registration_data: RegistrationData,
) -> None:
    """Registration fails if email format is invalid."""
    registration_data[User.USERNAME_FIELD] = 'email_invalid_format'
    response = client.post(path=URL_PATH, data=registration_data)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db()
def test_user_already_registered(
    client: Client,
    db_user: User,
    registration_data: RegistrationData,
) -> None:
    """Registration fails if user is already registered."""
    registration_data[User.USERNAME_FIELD] = db_user.email
    response = client.post(path=URL_PATH, data=registration_data)
    assert response.status_code == HTTPStatus.OK


@pytest.mark.django_db()
def test_registration_valid(
    client: Client,
    registration_data: RegistrationData,
    user_data: UserData,
    assert_correct_user: UserAssertion,
) -> None:
    """Registration is successful if all required fields are provided."""
    response = client.post(path=URL_PATH, data=registration_data)
    assert response.status_code == HTTPStatus.FOUND
    assert response.get('Location') == reverse('identity:login')
    assert_correct_user(registration_data['email'], user_data)


@pytest.mark.django_db()
@pytest.mark.slow()
@httpretty.activate
def test_registration_external_api(
    client: Client,
    registration_data: RegistrationData,
    user_data: UserData,
    user_external_api: ExternalAPIUserData,
    assert_correct_user_external_api: ExternalAPIUserAssertion,
) -> None:
    """
    Registration is successful if using external API.

    Users API url is redirected to external JSON Server.
    """
    httpretty.register_uri(
        method=httpretty.POST,
        uri=SETTINGS.DJANGO_USERS_API_URL,
        body=json.dumps(user_external_api),
        content_type='application/json',
    )
    response = client.post(path=URL_PATH, data=registration_data)
    assert response.status_code == HTTPStatus.FOUND
    assert_correct_user_external_api(user_external_api, user_data)
