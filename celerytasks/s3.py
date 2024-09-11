import boto3
import io
import os


class S3_DB:
    def __init__(self):
        self.key = os.environ.get('AWS_KEY')
        self.secret = os.environ.get('AWS_SECRET')
        self.ticket_bucket = os.environ.get('TICKET_BUCKET')
        self.s3_client = boto3.resource('s3', aws_access_key_id=self.key, aws_secret_access_key=self.secret)
        self.client = boto3.client('s3', aws_access_key_id=self.key, aws_secret_access_key=self.secret)
        self.bucket = self.s3_client.Bucket(self.ticket_bucket)
        
    def list_items(self, folderpath):
        files = []
        for f in self.bucket.objects.filter(Prefix=folderpath):
            filename = os.path.basename(f.key)
            if filename != "":
                files.append({'filename': filename, 'key': f.key})
        return files

    def download_file(self, item_path):
        fileObj = io.BytesIO()
        self.bucket.download_fileobj(item_path, fileObj)
        fileObj.seek(0)
        return fileObj

    def upload_file(self, item, path):
        self.bucket.upload_fileobj(item, path) 

    def ignore_file(self, copy_source, bucket, file):
        return self.client.copy(copy_source, bucket, file)

    def list_bucket_items(self, bucket, folderpath):
        bucket = self.s3_client.Bucket(bucket)
        return bucket.objects.filter(Prefix=folderpath)

    def getPresigned(self, bucket, file_name):
        presigned = self.client.generate_presigned_post(bucket, file_name, ExpiresIn=3600)
        print(presigned)
        return presigned

    def getDownloadPresigned(self, bucket_name, file_name):
        return self.client.generate_presigned_url('get_object', Params={'Bucket': bucket_name, 'Key': file_name}, ExpiresIn=300)

    def deleteFile(self, bucket_name, file_name):
        return self.client.delete_object(Bucket=bucket_name, Key=file_name)

    def tagItem(self, bucket_name, file_name, tagSet):
        return self.client.put_object_tagging(Bucket=bucket_name, Key=file_name,Tagging={'TagSet': tagSet})

    def copy_bucket_object(self, copy_source, bucket, file):
        return self.client.copy(copy_source, bucket, file)

    def list_bucket_objects(self, bucket_name):
        return self.client.list_objects(Bucket = bucket_name)["Contents"]

    def rename_images_to_be_unique(self, file_name, path):
        original_filename = file_name
        base_name, file_extension = os.path.splitext(original_filename)
        items = self.list_bucket_items(self.ticket_bucket, path)
        
        # Extract existing filenames in the bucket
        existing_files = []
        for item in items:
            existing_files.append(os.path.basename(item.key))
        
        # Start with the original filename
        new_filename = original_filename
        counter = 0
        
        # Check if the filename already exists
        while new_filename in existing_files:
            counter += 1
            new_filename = f"{base_name}({counter}){file_extension}"
        
        return new_filename