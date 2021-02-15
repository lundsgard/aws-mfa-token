from helpers import iam_login_default


def test__awstoken():
    iam_login_default('longterm-cred', 'AuditRole')

    assert 1 == 1
