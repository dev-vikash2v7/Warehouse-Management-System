import openai
import pandas as pd
import json
import logging
from typing import Dict, List, Any
import plotly.express as px
import plotly.graph_objects as go
import plotly.utils
from datetime import datetime, timedelta
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AIQueryEngine:
    def __init__(self, api_key: str = None):
        """Initialize AI Query Engine with OpenAI"""
        if api_key:
            openai.api_key = api_key
        else:
            # Try to get from environment
            import os
            # api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                openai.api_key = api_key
            else:
                logger.warning("No OpenAI API key provided")
        
        self.system_prompt = self._get_system_prompt()
        self.conversation_history = []
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI assistant"""
        return """You are an AI assistant for a Warehouse Management System (WMS). 
        You help users analyze sales data and generate insights using natural language.
        
        Available data tables:
        1. sales_data: Contains columns like Order_ID, SKU, MSKU, Quantity, Date, Channel, etc.
        2. mapping_data: Contains SKU to MSKU mappings
        
        Your capabilities:
        - Answer questions about sales data
        - Generate charts and visualizations
        - Provide data analysis insights
        - Help with data cleaning and mapping
        
        When asked to create charts, provide the chart data in JSON format with:
        - chart_type: "bar", "line", "pie", "scatter"
        - data: the data points
        - title: chart title
        - x_axis: x-axis label
        - y_axis: y-axis label
        
        Be helpful, accurate, and provide actionable insights."""
    
    def query(self, user_query: str, data_context: Dict[str, pd.DataFrame] = None) -> Dict[str, Any]:
        """Process natural language query and return response"""
        try:
            # Prepare context
            context = self._prepare_context(data_context)
            
            # Build messages
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": f"Context: {context}\n\nUser Query: {user_query}"}
            ]
            
            # Add conversation history
            if self.conversation_history:
                messages.extend(self.conversation_history[-4:])  # Last 4 exchanges
            
            # Call OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=messages,
                max_tokens=1000,
                temperature=0.3
            )
            
            ai_response = response.choices[0].message.content
            
            # Update conversation history
            self.conversation_history.extend([
                {"role": "user", "content": user_query},
                {"role": "assistant", "content": ai_response}
            ])
            
            # Parse response for chart requests
            chart_data = self._extract_chart_data(ai_response, data_context)
            
            return {
                'response': ai_response,
                'chart_data': chart_data,
                'query_type': self._classify_query(user_query),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing AI query: {e}")
            return {
                'response': f"Sorry, I encountered an error: {str(e)}",
                'chart_data': None,
                'query_type': 'error',
                'timestamp': datetime.now().isoformat()
            }
    
    def _prepare_context(self, data_context: Dict[str, pd.DataFrame]) -> str:
        """Prepare data context for AI"""
        if not data_context:
            return "No data available"
        
        context_parts = []
        
        for table_name, df in data_context.items():
            if df is not None and not df.empty:
                context_parts.append(f"{table_name}:")
                context_parts.append(f"- Columns: {list(df.columns)}")
                context_parts.append(f"- Rows: {len(df)}")
                context_parts.append(f"- Sample data: {df.head(3).to_dict('records')}")
        
        return "\n".join(context_parts)
    
    def _classify_query(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['chart', 'graph', 'plot', 'visualize']):
            return 'chart'
        elif any(word in query_lower for word in ['analyze', 'insight', 'trend']):
            return 'analysis'
        elif any(word in query_lower for word in ['count', 'total', 'sum']):
            return 'aggregation'
        elif any(word in query_lower for word in ['map', 'mapping', 'sku']):
            return 'mapping'
        else:
            return 'general'
    
    def _extract_chart_data(self, ai_response: str, data_context: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Extract chart data from AI response"""
        try:
            # Look for JSON chart data in response
            json_match = re.search(r'\{.*"chart_type".*\}', ai_response, re.DOTALL)
            if json_match:
                chart_data = json.loads(json_match.group())
                return self._generate_chart(chart_data, data_context)
            
            # If no JSON found, try to infer chart from query
            return None
            
        except Exception as e:
            logger.error(f"Error extracting chart data: {e}")
            return None
    
    def _generate_chart(self, chart_data: Dict[str, Any], data_context: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Generate chart using plotly based on AI specifications"""
        try:
            df = data_context.get('sales_data')
            if df is None or df.empty:
                return None
            
            chart_type = chart_data.get('chart_type', 'bar')
            title = chart_data.get('title', 'Chart')
            
            if chart_type == 'bar':
                # Top products chart
                top_products = df['MSKU'].value_counts().head(10)
                fig = px.bar(
                    x=top_products.values,
                    y=top_products.index,
                    orientation='h',
                    title=title,
                    labels={'x': 'Count', 'y': 'Product'}
                )
            
            elif chart_type == 'pie':
                # Mapping status chart
                mapping_status = df['MSKU'].apply(lambda x: 'Mapped' if x != 'Unmapped' else 'Unmapped').value_counts()
                fig = px.pie(
                    values=mapping_status.values,
                    names=mapping_status.index,
                    title=title
                )
            
            elif chart_type == 'line':
                # Time series chart
                if 'Date' in df.columns:
                    df['Date'] = pd.to_datetime(df['Date'])
                    daily_sales = df.groupby(df['Date'].dt.date).size()
                    fig = px.line(
                        x=daily_sales.index,
                        y=daily_sales.values,
                        title=title,
                        labels={'x': 'Date', 'y': 'Orders'}
                    )
                else:
                    return None
            
            else:
                return None
            
            return {
                'chart_json': json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder),
                'chart_type': chart_type,
                'title': title
            }
            
        except Exception as e:
            logger.error(f"Error generating chart: {e}")
            return None
    
    def analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform automated data analysis"""
        try:
            analysis = {
                'total_records': len(df),
                'unique_products': df['MSKU'].nunique() if 'MSKU' in df.columns else 0,
                'mapping_rate': 0,
                'top_products': {},
                'data_quality': {}
            }
            
            # Calculate mapping rate
            if 'MSKU' in df.columns:
                mapped_count = len(df[df['MSKU'] != 'Unmapped'])
                analysis['mapping_rate'] = (mapped_count / len(df)) * 100
                analysis['top_products'] = df['MSKU'].value_counts().head(5).to_dict()
            
            # Data quality checks
            analysis['data_quality'] = {
                'missing_values': df.isnull().sum().to_dict(),
                'duplicate_records': len(df[df.duplicated()]),
                'date_range': None
            }
            
            if 'Date' in df.columns:
                try:
                    df['Date'] = pd.to_datetime(df['Date'])
                    analysis['data_quality']['date_range'] = {
                        'start': df['Date'].min().strftime('%Y-%m-%d'),
                        'end': df['Date'].max().strftime('%Y-%m-%d')
                    }
                except:
                    pass
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing data: {e}")
            return {}
    
    def suggest_insights(self, df: pd.DataFrame) -> List[str]:
        """Generate insights from data"""
        insights = []
        
        try:
            if 'MSKU' in df.columns:
                # Mapping insights
                mapping_rate = (len(df[df['MSKU'] != 'Unmapped']) / len(df)) * 100
                if mapping_rate < 90:
                    insights.append(f"⚠️ Only {mapping_rate:.1f}% of SKUs are mapped. Consider updating your mapping file.")
                
                # Top product insights
                top_product = df['MSKU'].value_counts().index[0]
                top_count = df['MSKU'].value_counts().iloc[0]
                insights.append(f"🏆 {top_product} is your top-selling product with {top_count} orders.")
            
            if 'Date' in df.columns:
                try:
                    df['Date'] = pd.to_datetime(df['Date'])
                    recent_date = df['Date'].max()
                    days_ago = (datetime.now() - recent_date).days
                    if days_ago > 7:
                        insights.append(f"📅 Data is {days_ago} days old. Consider updating with recent sales data.")
                except:
                    pass
            
            if 'Quantity' in df.columns:
                total_quantity = df['Quantity'].sum()
                avg_quantity = df['Quantity'].mean()
                insights.append(f"📦 Total quantity sold: {total_quantity:,} units (avg: {avg_quantity:.1f} per order)")
            
        except Exception as e:
            logger.error(f"Error generating insights: {e}")
        
        return insights

# Example usage and testing
if __name__ == "__main__":
    # Initialize AI engine
    ai_engine = AIQueryEngine()
    
    # Sample data
    sample_data = {
        'sales_data': pd.DataFrame({
            'Order_ID': ['ORD001', 'ORD002', 'ORD003'],
            'SKU': ['SKU001', 'SKU002', 'SKU001'],
            'MSKU': ['MSKU001', 'MSKU002', 'MSKU001'],
            'Quantity': [2, 1, 3],
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03']
        })
    }
    
    # Test queries
    test_queries = [
        "Show me the top selling products",
        "What's the mapping rate?",
        "Create a bar chart of product sales",
        "Analyze the data quality"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = ai_engine.query(query, sample_data)
        print(f"Response: {response['response']}")
        print(f"Query Type: {response['query_type']}") 