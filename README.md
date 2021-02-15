## Configuration 

Modify $HOME\.aws\config with profile default:
```
[profile default]
region = eu-west-1
output = json
```

Modify $HOME\.aws\credentials with: 
```
[my-longterm-credentials]
aws_access_key_id = ACCCCCCCCCCCESS-KEY-ID
aws_secret_access_key = SEEEEEEEEEEEEEEEEEEEEEEECRET-ACCESS-KEY
username = iam@user.com
```

For usage of awstoken.py run:
```
python awstoken.py --help 
```

Typical usage:
```
python awstoken.py --role-name AuditRole --long-term-cred-profile my-longterm-credentials
```