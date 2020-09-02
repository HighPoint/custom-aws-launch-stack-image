import json
import cv2 as cv
import base64
import os
import boto3
import numpy as np

def lambda_handler(event, context):

  (sentText, saveToS3, bucketName, s3client, originalImage) = initProcess(event)

  outputImage = processImage(originalImage, sentText)

  if saveToS3:
    saveImageToS3(outputImage, sentText, bucketName, s3client)

  return returnJSON(outputImage)


# Initialize Setup

def initProcess(event):

  sentText = event.get('textInput',"")
  saveToS3 = event.get('saveToS3', True)
  bucketName = os.environ['BucketName']

  s3client = boto3.resource('s3')
  s3client.Bucket(bucketName).download_file('Launch-Stack-Icons/generic-launch-stack.png', '/tmp/original.png')

  # Read the image
  originalImage = cv.imread('/tmp/original.png', cv.IMREAD_UNCHANGED)


  return (sentText, saveToS3, bucketName, s3client, originalImage)


# Process Image

def processImage(originalImage, sentText):

  beginImage = originalImage[0:27,0:10]

  fontFace = cv.FONT_HERSHEY_SIMPLEX
  fontScale = 0.6
  fontThickness = 1

  length = cv.getTextSize(sentText, fontFace, fontScale, fontThickness)

  middleImage = cv.resize(originalImage[0:27,10:15], (int(length[0][0])+3, 27), interpolation = cv.INTER_AREA)
  middleImage = cv.putText(middleImage, sentText, (2,19), fontFace,
                   fontScale, ( 0, 0, 0, 255), fontThickness, cv.LINE_AA)

  endImage = originalImage[0:27, 110:144]

  outputImage = np.hstack((beginImage, middleImage, endImage))

  return outputImage


# Save Image To S3

def saveImageToS3(image, sentText, bucketName, s3client):

# first save the file from OpenCV then open it as a binary
  cv.imwrite("/tmp/save.png", image)

  f = open("/tmp/save.png", "rb")
  fileBody = f.read()

# remove the whitespace (if any) at the ends of the sent text and replace spaces with '-'
  key = sentText.strip().replace(' ','-') + ".png"

  Prefix = 'Launch-Stack-Icons/'

  s3 = boto3.resource('s3')

  if len(key) > 4:
    s3.Object(bucketName, Prefix + key).put(Body=fileBody)

  return


# Convert image to utf-8 encoded base64.
# First write the image

def convertImageToBase64(image):

  cv.imwrite("/tmp/output.png", image)

  with open('/tmp/output.png', "rb") as imageFile:
    str = base64.b64encode(imageFile.read())
    encoded_image = str.decode("utf-8")

  return encoded_image


# the return JSON

def returnJSON(image):

  encoded_image = convertImageToBase64(image)

  return {
      "isBase64Encoded": True,
      "statusCode": 200,

      "headers": { "content-type": "image/jpeg",
                   "Access-Control-Allow-Origin" : "*",
                   "Access-Control-Allow-Credentials" : True
      },
      "body":   encoded_image
    }
