# Read the Blog Post Tutorial
[Building a NBA Connections Web App with AI Tools](https://jman4190.medium.com/building-a-nba-connections-web-app-64a76a3faa35)

# NBA Connections Game

A daily word association game where players group NBA players by their shared characteristics. Inspired by the NYT Connections game but focused on NBA players and their unique attributes.

## Features

- Daily puzzles with 16 NBA players to group into 4 categories
- Progressive difficulty levels (Yellow → Green → Blue → Purple)
- Score tracking and sharing
- Mobile-responsive design
- Confetti celebration on wins! 🎉

## Tech Stack

- Frontend: Next.js 14 (App Router), TypeScript, Tailwind CSS
- Backend: Python (puzzle generation/validation), Supabase (database)
- APIs: OpenAI GPT-4, SearchAPI

## Prerequisites

- Node.js 18+
- Python 3.8+
- Supabase account
- OpenAI API key
- SearchAPI key

## Environment Setup

1. Clone the repository:
```bash
git clone https://github.com/your-username/nba-connections.git
cd nba-connections
```

2. Create `.env` file in the root directory:
```bash
NEXT_PUBLIC_SUPABASE_URL=your_supabase_url
NEXT_PUBLIC_SUPABASE_ANON_KEY=your_supabase_anon_key
NEXT_PUBLIC_SUPABASE_SERVICE_KEY=your_supabase_service_key
OPENAI_API_KEY=your_openai_api_key
SEARCHAPI_API_KEY=your_searchapi_key
```

3. Create `.env` file in the `backend` directory with the same variables.

## Database Setup

1. Create a new Supabase project
2. Run the SQL scripts from `backend/schemas/`:
```sql
-- Run themes.sql first
-- Then run puzzles.sql
```

## Installation

1. Install frontend dependencies:
```bash
npm install
```

2. Install backend dependencies:
```bash
cd backend
pip install -r requirements.txt
```

## Running the Application

1. Start the frontend development server:
```bash
npm run dev
```

2. Generate and validate themes:
```bash
cd backend
python theme_generator.py
python theme_validator.py
```

3. Generate puzzles:
```bash
python puzzle_manager.py
```

The app will be available at `http://localhost:3000`

## Puzzle Generation Pipeline

1. `theme_generator.py`: Creates themed groups of NBA players
2. `theme_validator.py`: Validates themes using NBA stats APIs
3. `puzzle_generator.py`: Assembles valid themes into puzzles
4. `puzzle_manager.py`: Orchestrates the pipeline and uploads to Supabase

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Inspired by the New York Times Connections game
- NBA data sourced from official NBA stats and Basketball Reference
- Built with ❤️ for NBA fans

## Support

For support, email your-email@example.com or open an issue in the repository.
