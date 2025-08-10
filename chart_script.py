import plotly.graph_objects as go
import plotly.express as px
import json

# Data from the provided JSON
data = {
    "factors": ["Development Speed", "Cross-platform Support", "Performance", "Resource Usage", "Community Support"], 
    "python_scores": [7, 8, 6, 5, 8], 
    "javascript_scores": [9, 9, 4, 3, 9]
}

# Shorten factor names to fit 15 character limit
shortened_factors = ["Dev Speed", "Cross-platform", "Performance", "Resource Usage", "Community"]

# Create horizontal grouped bar chart
fig = go.Figure()

# Add Python stack bars
fig.add_trace(go.Bar(
    y=shortened_factors,
    x=data["python_scores"],
    name="Python",
    orientation='h',
    marker_color='#1FB8CD',
    cliponaxis=False
))

# Add JavaScript stack bars
fig.add_trace(go.Bar(
    y=shortened_factors,
    x=data["javascript_scores"],
    name="JavaScript",
    orientation='h',
    marker_color='#DB4545',
    cliponaxis=False
))

# Update layout
fig.update_layout(
    title="Python vs JS: Audio Transcription",
    xaxis_title="Rating (1-10)",
    yaxis_title="Tech Factors",
    barmode='group',
    legend=dict(orientation='h', yanchor='bottom', y=1.05, xanchor='center', x=0.5)
)

# Update x-axis to show scale from 0 to 10
fig.update_xaxes(range=[0, 10], dtick=1)

# Save the chart
fig.write_image("tech_stack_comparison.png")