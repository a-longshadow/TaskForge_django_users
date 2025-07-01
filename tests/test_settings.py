import pytest
from tasks.models import AppSetting


@pytest.mark.django_db
def test_app_setting_get():
    AppSetting.objects.create(key="FOO", value="bar")
    assert AppSetting.get("FOO") == "bar"
    assert AppSetting.get("MISSING", default="x") == "x" 