
# Sandbox UI

This folder contains the "index.html" files that serve as the web interface for each data sandbox, under the folder matching its bucket name (e.g. the "index.html" file for the sandbox named "usdot-its-cvpilot-public-data" would be found in the [usdot-its-cvpilot-public-data/](usdot-its-cvpilot-public-data/) folder).

## Deployment of Sandbox UI (i.e. S3 Explorer site)

1. Upload `index.html` to the root folder of your S3 bucket.
2. In the AWS Console for your S3 bucket, go to "Permissions" > "CORS configuration" and copy and paste the following block of text and replace `{BUCKET_NAME}` with your bucket name.

```
<?xml version="1.0" encoding="UTF-8"?>
<CORSConfiguration xmlns="http://s3.amazonaws.com/doc/2006-03-01/">
<CORSRule>
    <AllowedOrigin>*</AllowedOrigin>
    <AllowedOrigin>http://{BUCKET_NAME}.s3.amazonaws.com</AllowedOrigin>
    <AllowedOrigin>https://s3.amazonaws.com</AllowedOrigin>
    <AllowedMethod>GET</AllowedMethod>
    <AllowedMethod>HEAD</AllowedMethod>
    <MaxAgeSeconds>3000</MaxAgeSeconds>
    <ExposeHeader>ETag</ExposeHeader>
    <ExposeHeader>x-amz-meta-custom-header</ExposeHeader>
    <AllowedHeader>Authorization</AllowedHeader>
    <AllowedHeader>*</AllowedHeader>
</CORSRule>
</CORSConfiguration>
```

3. Save. Also make sure that your bucket policy allows for List/Get actions on resource `arn:aws:s3:::{BUCKET_NAME}/*` and `arn:aws:s3:::{BUCKET_NAME}`.