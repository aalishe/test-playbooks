from argparse import ArgumentParser
import sys

ap = ArgumentParser()
ap.add_argument('--saml-user', dest='user', required=True)
ap.add_argument('--saml-user-password', dest='password', required=True)
_, saml_args = ap.parse_known_args()

saml = {"SOCIAL_AUTH_SAML_SP_PUBLIC_CERT": "-----BEGIN CERTIFICATE-----\nMIIFtTCCA52gAwIBAgIJAMWnzCA4dXpgMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV\nBAYTAkFVMRMwEQYDVQQIEwpTb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBX\naWRnaXRzIFB0eSBMdGQwHhcNMTcwOTIwMTQyNjQ5WhcNMTgwOTIwMTQyNjQ5WjBF\nMQswCQYDVQQGEwJBVTETMBEGA1UECBMKU29tZS1TdGF0ZTEhMB8GA1UEChMYSW50\nZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIIC\nCgKCAgEAv5WB0831GVYKu+H00iKYM8t1M376ifLiv4vJkM9tYDAv00Ja2757y8PW\nxBQG8o9CsmE/X+q13T+W0PY+apvjvlQGBBhnso/mJPwhWp2l3/EhAhVctqfO2Ilx\nPEgOqQF5+JX5Um/dvNyF3dfmFGuLg3J4ABfDwRMuJEMcQkSSZ5docZU5c3X6ISMf\nzWw9BDD7I6twxQkHj4TNjSFZv7K+PUUKwde3MEaDHzpDza7Kd9WrnCS9S/EZe9db\n4dki5NqluGvAf0pve8RHbsUDB4qO5HYDFCnj4niD3yKhMFW9Hwr8y8x0jFiCUupr\nlAz39Lmi4TTI5sOslaxCigaKRwMkoGAcQw45YFMpN6Ku6FVvIYVs+zND9gGUGb9M\nM0UQRvkNCR60RYL4fUvD76OsDUyuc/X5o8yG/2Wt4wCapxubQ1F8pIg8pP6tN4Xv\nm9Nk+350fXBoo2Q1DmkKs9kUEHT3gq2gMfVFS8fe/0VdJhDuCxUytf+YIbsHDHnO\nrV6Q6ZPsXml1542uMCcrdDXeL14QwK2bjMB7zDMvAJqHdNpqqekxBeSjayV1jLh+\nxaS23/KF7lS/ogJ0GF0x+3qTA2FRrG1FcPnaNnx5tATPgwRtXamGmVaB+qWRVpHe\ntdJLJcJA4mIWeOsVN3vC7GLVsZxCZmuO3jZzGdcKSRP/j3sitdkCAwEAAaOBpzCB\npDAdBgNVHQ4EFgQUaekzRlkJvxNiCMqWWD5+noL+lk4wdQYDVR0jBG4wbIAUaekz\nRlkJvxNiCMqWWD5+noL+lk6hSaRHMEUxCzAJBgNVBAYTAkFVMRMwEQYDVQQIEwpT\nb21lLVN0YXRlMSEwHwYDVQQKExhJbnRlcm5ldCBXaWRnaXRzIFB0eSBMdGSCCQDF\np8wgOHV6YDAMBgNVHRMEBTADAQH/MA0GCSqGSIb3DQEBBQUAA4ICAQBbl8vkxDSi\np6g4w4ydltP3xi4q+ZxjeVvIb1V7MkPLIc9YAWfDtc0BEYJYQIBta2KxKG0La4is\nERbjgedZUIrmT3d0JoUH7IWT2s4M020eSVAuqwliqy3hi7BsFBIx80Ukd3fzX45U\nZ/vrqR39YlGXAJ8Hwv1o5jSTlFNslliHXe33MshXVGpwvYCVTDuWsKkYz7crnhjm\nFXTF1M7WGOLSA41au//o1SThx8SgYdYPx6fMm6YblpVX6GvtQrHhnFMP3raOfYuc\nlkuDY2IXYn+3vfD2bd8DtfuoQl/BiWYSl3eMYEt8BHITkLcdotsG/I0vrCRv5WLu\nngbW7gQoSmQoDfWV55F6IcX796Sd/7/jgZjdYQ6TKjP2d7kdKCDQEFwRSQBYzerA\nOGrVGmZ56c+pzoyN3cLAsSZVZa1SUjNcMIEqKUuYCjYCMFurxnupe0pwJbBqjzOC\n1HRs6qdQfyegbsx4kB5AeEsseLkotKDGqfo0uqQeybFRs3jlzb6MMf/mJtz+D9T2\npa9NeP8bn9cc3Rpf3guNtnl0/6v7W6JYktFmJ7g299LYOqIHuS8J8l53MGHPaqQn\nbd/JsUF2c1x9yCVq+1MHdOuahJH3/3XAgZkcez1p3ePriYa9HRAcw97GVO34rGPn\nAOfoJTzJqCQVUlNgSy3JZw8U5bycRWDQAA==\n-----END CERTIFICATE-----",
        "SOCIAL_AUTH_SAML_SP_PRIVATE_KEY": "-----BEGIN RSA PRIVATE KEY-----\n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\n-----END RSA PRIVATE KEY-----",
        "SOCIAL_AUTH_SAML_ORG_INFO": {
            "en-US": {
                "url": "http://www.example.com",
                "displayname": "Example",
                "name": "example"
            }
        },
        "SOCIAL_AUTH_SAML_TECHNICAL_CONTACT": {
            "givenName": "Some User",
            "emailAddress": "suser@example.com"
        },
        "SOCIAL_AUTH_SAML_SUPPORT_CONTACT": {
            "givenName": "Some User",
            "emailAddress": "suser@example.com"
        },
        "SOCIAL_AUTH_SAML_SP_ENTITY_ID": tkit_args.base_url,
        "SOCIAL_AUTH_SAML_ENABLED_IDPS": {
            "ipsilon": {
                "attr_last_name": "surname",
                "attr_username": "name_id",
                "entity_id": "https://idp.testing.ansible.com/idp/saml2/metadata",
                "attr_user_permanent_id": "name_id",
                "url": "https://idp.testing.ansible.com/idp/saml2/SSO/Redirect",
                "attr_email": "email",
                "x509cert": "MIIDFzCCAf+gAwIBAgIJAJ6GJKpQRVEvMA0GCSqGSIb3DQEBCwUAMCIxIDAeBgNV\nBAMMF2lkcC50ZXN0aW5nLmFuc2libGUuY29tMB4XDTE4MDExNTE3MTA0NVoXDTIz\nMDExNDE3MTA0NVowIjEgMB4GA1UEAwwXaWRwLnRlc3RpbmcuYW5zaWJsZS5jb20w\nggEiMA0GCSqGSIb3DQEBAQUAA4IBDwAwggEKAoIBAQDNNyHbi6WuVd52pvz/eVf+\n6Hq6YkUM+uXSdWXmvbDmLy20SLgxSSHvW+1bIp23cB4hDMQhoc6zIfn68pllUDM3\nSeIcKRR8PXeXpEgoZ+inyajCtvHkg1o5JGBULoRNH10GqsPD8f7FBvXpQ1YJHGeD\ncHDFX/+LFCSypfv9Qvchc78cjG26kr/ofrJLOwvu6uiak8UsWAHpHlEcfVHGBRSx\nKWTcxEPYmuKXXivM5llonKeuzaacrfoeDisJu3P1dw4DAO2Cjc7zbEenG/dfHXEv\n0ct13e2OF0DzKXXwxfspjaIPRmJhWf7LQMm7RK4atSNow2lEszTt03cglD1nWX0l\nAgMBAAGjUDBOMB0GA1UdDgQWBBQ4PG0oMiW4jOiJNpyg8AQhxKvMqjAfBgNVHSME\nGDAWgBQ4PG0oMiW4jOiJNpyg8AQhxKvMqjAMBgNVHRMEBTADAQH/MA0GCSqGSIb3\nDQEBCwUAA4IBAQC2cRv5NAzOvG/PUBLUS5ePBcZH0wVTkEtint4I0IoF7P0oAdP2\nZ4InbqGBfjFAruVjVhoQxcu05S779XjSgdaFNURuURA3K1E1iffzv8453UAxOnLm\nglr5dRJGto0NbjxYPsZtaHtpN4OsHHwKbYb//nbFTYytBjz+/PvizBwA8y+RLuBk\ns4/+pU6VBjPQldDfYVCxx10GOx989AeVcFjO48EpljKOpQ7+6jLbRpWQg5up6i9C\nwY1BI5H+WSc7RQ3aoR3KQ1B/HnOXJyseSD/w5De3kDv+XnlZfFh542KxiTBLqw+D\nBg/h1nSriyIebXaY+09wSztE8xD9Ypq5Jf0j",
                "attr_first_name": "givenname"
            }
        },
        "SOCIAL_AUTH_SAML_ORGANIZATION_MAP": {},
        "SOCIAL_AUTH_SAML_TEAM_MAP": {}
}

saml_settings = v2.settings.get().get_setting('saml')
saml_settings.patch(**saml)
