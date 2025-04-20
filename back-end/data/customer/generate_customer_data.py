import pandas as pd
import numpy as np
from faker import Faker
import random
from datetime import datetime

# Initialize Faker
fake = Faker('ko_KR')

def generate_customer_data(num_customers=1000):
    # Define possible values for categorical variables
    investment_tendencies = ['Conservative', 'Moderate', 'Aggressive']
    financial_statuses = ['Poor', 'Fair', 'Good', 'Excellent']
    risk_tolerances = ['Low', 'Medium', 'High']
    investment_horizons = ['Short-term (1-3 years)', 'Medium-term (3-5 years)', 'Long-term (5+ years)']
    
    # ETF list (example ETFs)
    etf_list = [
        'KODEX 200', 'TIGER 200', 'KODEX 코스닥150', 'TIGER 미국S&P500',
        'KODEX 미국나스닥100', 'TIGER 유로스탁스50', 'KODEX 일본TOPIX100',
        'TIGER 중국CSI300', 'KODEX 인도Nifty50'
    ]
    
    data = []
    
    for _ in range(num_customers):
        age = random.randint(20, 70)
        name = fake.name()
        investment_tendency = random.choices(investment_tendencies, weights=[0.4, 0.4, 0.2])[0]
        financial_status_category = random.choices(financial_statuses, weights=[0.2, 0.3, 0.3, 0.2])[0]
        has_etf = random.choices([True, False], weights=[0.6, 0.4])[0]
        
        # Generate financial status details
        income = random.randint(30000000, 150000000) // 1000000 * 1000000  # Rounded to nearest million
        savings = random.randint(10000000, 500000000) // 1000000 * 1000000  # Rounded to nearest million
        monthly_investment = random.randint(100000, 1000000) // 10000 * 10000  # Rounded to nearest 10,000
        
        # Generate ETF holdings if customer has ETFs
        current_etf_holdings = []
        if has_etf:
            num_holdings = random.randint(1, 3)
            current_etf_holdings = random.sample(etf_list, num_holdings)
        
        risk_tolerance = random.choices(risk_tolerances, weights=[0.4, 0.4, 0.2])[0]
        investment_horizon = random.choices(investment_horizons, weights=[0.3, 0.4, 0.3])[0]
        
        customer = {
            'customer_id': fake.uuid4(),
            'age': age,
            'name': name,
            'investment_tendency': investment_tendency,
            'financial_status': {
                'category': financial_status_category,
                'income': income,
                'savings': savings,
                'monthly_investment': monthly_investment
            },
            'has_etf': has_etf,
            'current_etf_holdings': ','.join(current_etf_holdings) if current_etf_holdings else '',
            'risk_tolerance': risk_tolerance,
            'investment_horizon': investment_horizon,
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        data.append(customer)
    
    # Convert to DataFrame
    df = pd.DataFrame(data)
    
    # Save to CSV
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'customer_data_{timestamp}.csv'
    df.to_csv(f'data/customer/{filename}', index=False, encoding='utf-8')
    
    return df

if __name__ == "__main__":
    df = generate_customer_data(1000)
    print(f"Generated {len(df)} customer records") 