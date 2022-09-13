terraform {
  required_version = ">= 0.12.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-2"
}

resource "random_string" "prefix" {
  length  = 8
  special = false
  upper   = false
}

resource "aws_s3_bucket" "my_bucket" {
  bucket_prefix = random_string.prefix.result
}

resource "aws_s3_bucket_acl" "my_bucket" {
  bucket = aws_s3_bucket.my_bucket.bucket
  acl    = "private"
}
