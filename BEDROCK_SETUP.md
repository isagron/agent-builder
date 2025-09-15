# AWS Bedrock Setup Guide

This guide helps you set up AWS Bedrock for the document indexing feature.

## Prerequisites

1. **AWS Account**: You need an AWS account with access to Bedrock
2. **Bedrock Access**: Request access to Bedrock foundation models in your AWS region
3. **AWS Credentials**: Configure AWS credentials on your system

## Step 1: Request Bedrock Access

1. Go to the [AWS Bedrock Console](https://console.aws.amazon.com/bedrock/)
2. Navigate to "Model access" in the left sidebar
3. Request access to the embedding models you want to use:
   - `amazon.titan-embed-text-v1` (recommended)
   - `amazon.titan-embed-text-v2`
   - `cohere.embed-english-v3`
   - `cohere.embed-multilingual-v3`

## Step 2: Configure AWS Credentials

Choose one of the following methods:

### Option A: AWS CLI (Recommended)
```bash
aws configure
```
Enter your:
- AWS Access Key ID
- AWS Secret Access Key
- Default region (e.g., `us-east-1`)
- Default output format (e.g., `json`)

### Option B: Environment Variables
```bash
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
export AWS_DEFAULT_REGION=us-east-1
```

### Option C: AWS Profile
```bash
aws configure --profile your-profile-name
export AWS_PROFILE=your-profile-name
```

## Step 3: Configure Bedrock Settings

Create a `.env` file in your project root:

```bash
# Bedrock Configuration
DOC_INDEX_IMPLEMENTATION=bedrock
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE=your-profile-name  # Optional, if using a specific profile
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v1
```

## Step 4: Test the Setup

Run the test script to verify everything is working:

```bash
python test_bedrock_setup.py
```

## Step 5: Start the Server

The server will automatically use Bedrock if configured:

```bash
python main.py
```

## Troubleshooting

### "The security token included in the request is invalid"
- Check your AWS credentials are correct
- Verify the AWS region is correct
- Ensure your AWS account has Bedrock access

### "AccessDenied" errors
- Request access to Bedrock models in the AWS console
- Check your IAM permissions include Bedrock access

### "Model not found" errors
- Verify the model ID is correct
- Check the model is available in your region
- Some models may not be available in all regions

## Available Models

### Amazon Titan Embeddings
- `amazon.titan-embed-text-v1` - General purpose text embeddings
- `amazon.titan-embed-text-v2` - Improved version with better performance

### Cohere Embeddings
- `cohere.embed-english-v3` - English text embeddings
- `cohere.embed-multilingual-v3` - Multilingual text embeddings

## Cost Considerations

- Bedrock charges per token for embedding generation
- Consider the number of documents and their size
- Monitor usage in the AWS Cost Explorer
- Start with a small document set for testing

## Fallback to Sentence Transformers

If Bedrock is not available, the system will automatically fall back to Sentence Transformers:

```bash
# Force Sentence Transformers
export DOC_INDEX_IMPLEMENTATION=sentence_transformers
```

This uses local models and doesn't require AWS credentials.
