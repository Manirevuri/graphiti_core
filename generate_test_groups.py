#!/usr/bin/env python3
import json
import datetime

# Base template for different scenarios
scenarios = [
    {
        "group_id": "healthcare_ai_group",
        "theme": "Healthcare AI Implementation",
        "person": "Dr. Sarah Johnson",
        "company": "MedPlus Healthcare",
        "project": "AI-powered diagnostic system",
        "technology": "TensorFlow and computer vision"
    },
    {
        "group_id": "fintech_ml_group", 
        "theme": "Financial Machine Learning",
        "person": "Alex Rodriguez",
        "company": "FinanceCore",
        "project": "fraud detection system",
        "technology": "scikit-learn and anomaly detection"
    },
    {
        "group_id": "retail_analytics_group",
        "theme": "Retail Analytics Platform",
        "person": "Maria Chen", 
        "company": "RetailTech Solutions",
        "project": "customer behavior prediction model",
        "technology": "PyTorch and recommendation systems"
    },
    {
        "group_id": "automotive_ai_group",
        "theme": "Autonomous Vehicle Systems", 
        "person": "James Wilson",
        "company": "AutoDrive Inc",
        "project": "self-driving car perception system",
        "technology": "OpenCV and neural networks"
    },
    {
        "group_id": "education_tech_group",
        "theme": "Educational Technology",
        "person": "Dr. Lisa Park",
        "company": "EduAI Systems",
        "project": "personalized learning platform",
        "technology": "natural language processing"
    },
    {
        "group_id": "energy_optimization_group", 
        "theme": "Smart Grid Optimization",
        "person": "Michael Kumar",
        "company": "GreenTech Energy",
        "project": "power consumption prediction model",
        "technology": "time series analysis and LSTM"
    },
    {
        "group_id": "cybersecurity_ml_group",
        "theme": "Cybersecurity Machine Learning",
        "person": "Rachel Thompson",
        "company": "SecureNet Solutions", 
        "project": "threat detection system",
        "technology": "ensemble methods and real-time processing"
    },
    {
        "group_id": "manufacturing_iot_group",
        "theme": "Industrial IoT Analytics",
        "person": "David Zhang",
        "company": "ManufactureTech",
        "project": "predictive maintenance system",
        "technology": "sensor data analysis and machine learning"
    },
    {
        "group_id": "social_media_group",
        "theme": "Social Media Analytics", 
        "person": "Emma Davis",
        "company": "SocialInsights Corp",
        "project": "sentiment analysis platform",
        "technology": "BERT and transformer models"
    },
    {
        "group_id": "video_content_group",
        "theme": "Video Content Analysis",
        "person": "Dr. Robert Kim",
        "company": "VideoAI Labs", 
        "project": "automated video summarization system",
        "technology": "computer vision and natural language generation"
    }
]

def generate_test_data(scenario):
    """Generate test data for a specific scenario"""
    base_time = datetime.datetime(2024, 1, 15, 10, 0, 0)
    
    messages = [
        {
            "content": f"Hi, I'm {scenario['person']}, working at {scenario['company']}. I'm leading a {scenario['theme'].lower()} initiative focused on {scenario['project']}.",
            "role_type": "user",
            "role": scenario['person'].split()[0],
            "timestamp": base_time.isoformat() + "Z",
            "name": "Project introduction",
            "source_description": "Team lead introduction"
        },
        {
            "content": f"That's fascinating! Can you tell me more about the {scenario['project']} you're building? What's your approach to implementing this technology?",
            "role_type": "assistant", 
            "role": "Assistant",
            "timestamp": (base_time + datetime.timedelta(minutes=1)).isoformat() + "Z",
            "name": "Project inquiry",
            "source_description": "Assistant response"
        },
        {
            "content": f"We're using {scenario['technology']} to build a robust solution. The main challenge is integrating with existing systems at {scenario['company']} while ensuring scalability and performance.",
            "role_type": "user",
            "role": scenario['person'].split()[0], 
            "timestamp": (base_time + datetime.timedelta(minutes=2)).isoformat() + "Z",
            "name": "Technical details",
            "source_description": "Technical implementation details"
        },
        {
            "content": f"What kind of data sources are you working with for the {scenario['project']}? Are there any specific compliance or privacy considerations for {scenario['theme'].lower()}?",
            "role_type": "assistant",
            "role": "Assistant", 
            "timestamp": (base_time + datetime.timedelta(minutes=3)).isoformat() + "Z",
            "name": "Data and compliance inquiry",
            "source_description": "Assistant inquiry about data"
        },
        {
            "content": f"Great question! We're processing multiple data streams and have implemented strict data governance protocols. The team at {scenario['company']} has developed custom APIs to handle the integration seamlessly while maintaining security standards.",
            "role_type": "user",
            "role": scenario['person'].split()[0],
            "timestamp": (base_time + datetime.timedelta(minutes=4)).isoformat() + "Z", 
            "name": "Data governance response",
            "source_description": "Data and security implementation"
        }
    ]
    
    return {
        "group_id": scenario["group_id"],
        "messages": messages
    }

# Generate all test files
for i, scenario in enumerate(scenarios):
    test_data = generate_test_data(scenario)
    filename = f"test_group_{i+1:02d}_{scenario['group_id']}.json"
    
    with open(filename, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    print(f"Generated {filename} for {scenario['theme']}")

print(f"\nGenerated {len(scenarios)} test group files!")