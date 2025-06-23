# School Reports Analytics Web App

A Streamlit web application that allows users to upload school reports in PDF format and visualize school performance trends over time.

## Features

- Upload multiple school reports in PDF format
- Extract metadata and performance indicators from PDF content
- Analyze performance indicators (Very Good, Good, Needs Improvement)
- Visualize trends across reports, semesters, and years
- Privacy-focused: no personal data is stored or processed
- Export data to CSV for further analysis

## Setup and Installation (Local Development)

1. Clone the repository:
   ```
   git clone <url>
   cd education_report_analyser
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Run the Streamlit app:
   ```
   streamlit run app.py
   ```

## Usage

1. Upload one or more school report PDFs using the file uploader
2. The app will automatically extract metadata and performance indicators from the PDF content
3. View the generated charts showing performance trends over time
4. Optionally export the data to CSV for further analysis

## Data Extraction

The application extracts the following information from the PDF content:

### Metadata Extraction
- Year
- Semester
- Report number

The app uses regex pattern matching to identify metadata in the PDF text using the pattern: "Semester X, YYYY - Progress Report Z"

### Performance Indicator Extraction
The app extracts performance indicators by:
1. Identifying tables in the PDF that contain assessment data
2. Analyzing each cell in these tables to count occurrences of:
   - "Very Good"
   - "Good (meets expectations)"
   - "Needs Improvement" or similar phrases

If tables cannot be properly extracted, the app will notify the user.

![Graph Image](assets/graph.png)

## Deployment to Streamlit Cloud

1. Push your code to GitHub:
   ```
   git remote add origin <url>
   git branch -M main
   git push -u origin main
   ```

2. Deploy to Streamlit Cloud:
   - Go to [Streamlit Cloud](https://streamlit.io/cloud)
   - Sign in with your GitHub account
   - Click "New app"
   - Select your repository, branch (main), and the main file path (app.py)
   - Click "Deploy"

3. Access your app:
   - Once deployed, your app will be available at a URL like: `https://xxxxx.streamlit.app`
   - The app is now publicly accessible (or can be password-protected through Streamlit Cloud settings)

## Privacy

- No personal student or teacher information is processed
- All data is processed in-memory during the session
- No data is stored long-term
- Session data is cleared upon browser refresh or session end

## Dependencies

The application uses the following main dependencies:
- streamlit>=1.22.0
- pandas>=1.5.3
- numpy>=1.24.3
- matplotlib>=3.7.1
- plotly>=5.14.1
- PyMuPDF>=1.21.1

## Streamlit Cloud Limitations

- Free tier provides 1GB RAM which is sufficient for most PDF processing
- No persistent storage (all data exists only during the user session)
- App restarts when new code is pushed to GitHub

## License

MIT 