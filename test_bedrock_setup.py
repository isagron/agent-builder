#!/usr/bin/env python3
"""Test script to verify Bedrock setup and configuration."""

import os
import asyncio
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_bedrock_setup():
    """Test Bedrock configuration and connectivity."""
    print("🔧 Testing Bedrock setup...")
    
    # Check environment variables
    print("\n📋 Environment Variables:")
    print(f"AWS_DEFAULT_REGION: {os.getenv('AWS_DEFAULT_REGION', 'Not set')}")
    print(f"AWS_PROFILE: {os.getenv('AWS_PROFILE', 'Not set')}")
    print(f"BEDROCK_EMBEDDING_MODEL: {os.getenv('BEDROCK_EMBEDDING_MODEL', 'Not set')}")
    
    # Check if required packages are installed
    print("\n📦 Package Availability:")
    try:
        import boto3
        print("✅ boto3: Available")
    except ImportError:
        print("❌ boto3: Not available")
        return
    
    try:
        import langchain_aws
        print("✅ langchain_aws: Available")
    except ImportError:
        print("❌ langchain_aws: Not available")
        return
    
    try:
        import faiss
        print("✅ faiss: Available")
    except ImportError:
        print("❌ faiss: Not available")
        return
    
    # Test Bedrock client creation
    print("\n🔗 Testing Bedrock Client:")
    try:
        import boto3
        from botocore.exceptions import NoCredentialsError, ClientError
        
        # Create Bedrock client
        region = os.getenv('AWS_DEFAULT_REGION', 'us-east-1')
        profile = os.getenv('AWS_PROFILE')
        
        if profile:
            session = boto3.Session(profile_name=profile)
            bedrock = session.client('bedrock-runtime', region_name=region)
            print(f"✅ Bedrock client created with profile '{profile}' in region '{region}'")
        else:
            bedrock = boto3.client('bedrock-runtime', region_name=region)
            print(f"✅ Bedrock client created with default credentials in region '{region}'")
        
        # Test list foundation models
        try:
            response = bedrock.list_foundation_models()
            models = response.get('modelSummaries', [])
            embedding_models = [m for m in models if 'embed' in m.get('modelId', '').lower()]
            print(f"✅ Found {len(embedding_models)} embedding models available")
            
            # Check if our target model is available
            target_model = os.getenv('BEDROCK_EMBEDDING_MODEL', 'amazon.titan-embed-text-v1')
            available_model_ids = [m['modelId'] for m in embedding_models]
            if target_model in available_model_ids:
                print(f"✅ Target model '{target_model}' is available")
            else:
                print(f"⚠️ Target model '{target_model}' not found in available models")
                print(f"Available embedding models: {available_model_ids[:5]}...")
                
        except ClientError as e:
            print(f"❌ Error listing models: {e}")
            if "AccessDenied" in str(e):
                print("💡 This might be a permissions issue. Check your AWS credentials.")
            return
            
    except NoCredentialsError:
        print("❌ No AWS credentials found")
        print("💡 Set up AWS credentials using:")
        print("   - AWS CLI: aws configure")
        print("   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
        print("   - AWS profile: AWS_PROFILE")
        return
    except Exception as e:
        print(f"❌ Error creating Bedrock client: {e}")
        return
    
    # Test document index creation
    print("\n📚 Testing Document Index Creation:")
    try:
        from app.services.doc_index_factory import create_document_index
        
        # Force Bedrock implementation
        doc_index = create_document_index(doc_root="doc", implementation="bedrock")
        print("✅ Document index created successfully")
        
        # Test initialization
        print("🚀 Testing initialization...")
        await doc_index.initialize()
        print("✅ Document index initialized successfully")
        
    except Exception as e:
        print(f"❌ Error with document index: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_bedrock_setup())
