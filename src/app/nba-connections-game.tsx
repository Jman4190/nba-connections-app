"use client";

import React, { useState, useEffect, useCallback } from 'react'
import confetti from 'canvas-confetti'
import { Button } from "@/components/ui/button"
import { LightbulbIcon, BarChart3Icon, HelpCircleIcon, XIcon, StarIcon, Menu, X, ArrowUpRight } from 'lucide-react'
import { useToast } from "@/components/ui/use-toast"
import { Toaster } from "@/components/ui/toaster"
import { motion, AnimatePresence } from 'framer-motion'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { createClient } from '@supabase/supabase-js'
import BasketballIcon from '@/components/ui/BasketballIcon'
import Link from 'next/link'

interface WordTile {
  word: string
  isSelected: boolean
  group?: string
  isAnimating?: boolean
  isShaking?: boolean
}

interface Group {
  words: string[];
  theme: string;
  color: string;
  emoji: string;
}

interface Guess {
  selectedWords: string[];
  isCorrect: boolean;
}

interface Puzzle {
  puzzle_id: number;
  date: string;
  groups: Group[];
  author: string;
}

const supabaseUrl = process.env.SUPABASE_URL
const supabaseKey = process.env.SUPABASE_KEY

// For client-side components, we need NEXT_PUBLIC_ prefix
const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL || supabaseUrl || '',
  process.env.NEXT_PUBLIC_SUPABASE_KEY || supabaseKey || ''
)

export default function NBAConnectionsGame() {
  const [gamePhase, setGamePhase] = useState<'loading' | 'ready' | 'playing'>('loading');
  const [tiles, setTiles] = useState<WordTile[]>([])
  const [mistakes, setMistakes] = useState(4)
  const [completedGroups, setCompletedGroups] = useState<Group[]>([])
  const [showResults, setShowResults] = useState(false)
  const { toast } = useToast()
  const [guesses, setGuesses] = useState<Guess[]>([])
  const [gameFinished, setGameFinished] = useState(false)
  const [showConfetti, setShowConfetti] = useState(false)
  const [showHowToPlay, setShowHowToPlay] = useState(false)
  const [puzzle, setPuzzle] = useState<Puzzle | null>(null);
  const [justEnded, setJustEnded] = useState(false);

  useEffect(() => {
    fetchPuzzleOfTheDay();
  }, []); // This effect runs once when the component mounts

  const fetchPuzzleOfTheDay = async () => {
    // Get local date in YYYY-MM-DD format
    const today = new Date();
    const year = today.getFullYear();
    const month = String(today.getMonth() + 1).padStart(2, '0');
    const day = String(today.getDate()).padStart(2, '0');
    const formattedDate = `${year}-${month}-${day}`;
    
    console.log('Fetching puzzle for date:', formattedDate);

    const { data, error } = await supabase
      .from('puzzles')
      .select('*')
      .eq('date', formattedDate)
      .single();

    if (error) {
      console.error('Error fetching puzzle:', error);
      return;
    }

    console.log('Fetched puzzle data:', data);
    if (data && Array.isArray(data.groups)) {
      setPuzzle(data);
      setGamePhase('ready');
    } else {
      console.error('Invalid puzzle data structure:', data);
    }
  };

  useEffect(() => {
    if (puzzle && Array.isArray(puzzle.groups)) {
      const initialTiles = puzzle.groups.flatMap(group => 
        Array.isArray(group.words) 
          ? group.words.map(word => ({ word, isSelected: false }))
          : []
      )
      setTiles(shuffleArray(initialTiles))
    } else {
      console.error('Puzzle data is not in the expected format:', puzzle)
    }
  }, [puzzle]);

  const shuffleArray = (array: any[]) => {
    const newArray = [...array]
    for (let i = newArray.length - 1; i > 0; i--) {
      const j = Math.floor(Math.random() * (i + 1));
      [newArray[i], newArray[j]] = [newArray[j], newArray[i]]
    }
    return newArray
  }

  const handleTileClick = (index: number) => {
    const selectedCount = tiles.filter(tile => tile.isSelected).length
    if (selectedCount >= 4 && !tiles[index].isSelected) return

    const newTiles = [...tiles]
    newTiles[index].isSelected = !newTiles[index].isSelected
    setTiles(newTiles)
  }

  const handleSubmit = () => {
    const selectedWords = tiles.filter(tile => tile.isSelected).map(tile => tile.word);
    if (selectedWords.length !== 4) return;

    // Check if this exact guess has been made before
    if (guesses.some(guess =>
      JSON.stringify(guess.selectedWords.sort()) === JSON.stringify(selectedWords.sort())
    )) {
      toast({
        description: "You've already tried this combination. Change at least one player.",
        duration: 2000,
      });
      return;
    }

    const matchingGroup = puzzle?.groups.find(group =>
      group.words.every(word => selectedWords.includes(word))
    );

    const newGuess: Guess = {
      selectedWords,
      isCorrect: !!matchingGroup
    };

    setGuesses([...guesses, newGuess]);

    // Sort selected tile indices from top-left to bottom-right
    const sortedSelectedIndices = tiles
      .map((tile, idx) => ({ tile, idx }))
      .filter(item => item.tile.isSelected)
      .sort((a, b) => a.idx - b.idx)
      .map(item => item.idx);

    // Animate selected tiles in sorted order
    sortedSelectedIndices.forEach((tileIndex, index) => {
      setTimeout(() => {
        setTiles(prevTiles => {
          const newTiles = [...prevTiles];
          newTiles[tileIndex] = { ...newTiles[tileIndex], isAnimating: true };
          return newTiles;
        });
      }, index * 200);
    });

    setTimeout(() => {
      if (matchingGroup) {
        rearrangeTilesForCorrectGuess(matchingGroup);
        const newCompletedGroups = [...completedGroups, matchingGroup];
        setCompletedGroups(newCompletedGroups);
        
        const newTiles = tiles.filter(tile => !selectedWords.includes(tile.word))
        const completedTiles = tiles.filter(tile => selectedWords.includes(tile.word))
          .map(tile => ({ ...tile, isSelected: false, group: matchingGroup.theme, isAnimating: false }))
        
        setTiles([...completedTiles, ...shuffleArray(newTiles)])
      } else {
        const newMistakes = mistakes - 1;
        setMistakes(newMistakes);
        
        // Check if they were one away from any group
        const maxCorrectWords = puzzle?.groups.reduce((max, group) => {
          const correctWords = selectedWords.filter(word => group.words.includes(word)).length;
          return Math.max(max, correctWords);
        }, 0) || 0;

        // Show appropriate toast based on remaining mistakes and correctness
        if (maxCorrectWords === 3) {
          toast({
            description: "One away...",
            duration: 2000,
          });
        } else {
          toast({
            description: "Turnover! Try again.",
            duration: 2000,
          });
        }

        // If this was the last mistake, trigger finish sequence
        if (newMistakes === 0) {
          finishGame();
          return;
        }
        
        // Shake incorrect tiles
        setTiles(prevTiles => prevTiles.map(tile => ({ ...tile, isShaking: selectedWords.includes(tile.word), isAnimating: false })))
        setTimeout(() => {
          setTiles(prevTiles => prevTiles.map(tile => ({ ...tile, isShaking: false })))
        }, 500)
      }
    }, sortedSelectedIndices.length * 200 + 500);
  }

  const rearrangeTilesForCorrectGuess = (group: Group) => {
    const groupIndex = puzzle?.groups.indexOf(group) || 0;
    const targetRowStart = groupIndex * 4;

    group.words.forEach((word, i) => {
      const currentIndex = tiles.findIndex(tile => tile.word === word);
      const targetIndex = targetRowStart + i;

      if (currentIndex === -1 || currentIndex === targetIndex) return;

      const targetTile = tiles[targetIndex];
      if (targetTile.group) return;

      setTiles(prevTiles => {
        const newTiles = [...prevTiles];
        [newTiles[currentIndex], newTiles[targetIndex]] = [newTiles[targetIndex], newTiles[currentIndex]];
        return newTiles;
      });
    });
  }

  const finishGame = useCallback(() => {
    const remainingGroups = puzzle?.groups.filter(group => !completedGroups.includes(group)) || [];
    const isWin = mistakes > 0 && completedGroups.length === puzzle?.groups.length;
    
    // Show appropriate toast based on game outcome
    if (!isWin) {
      toast({
        description: "Better luck next time!",
        duration: 2000,
      });
    } else {
      toast({
        description: "Slam Dunk! You won!",
        duration: 2000,
      });
    }

    // Deselect all tiles after toast
    setTimeout(() => {
      setTiles(prevTiles => prevTiles.map(tile => ({ ...tile, isSelected: false })));
      setGameFinished(true);
      
      // For wins, go straight to results and fire confetti
      if (isWin) {
        setJustEnded(true);
        setTimeout(() => {
          setShowConfetti(true);
          setTimeout(() => setShowConfetti(false), 5000);
          setShowResults(true);
        }, 1000);
        return;
      }

      // For losses, reveal remaining groups one by one
      remainingGroups.forEach((group, index) => {
        setTimeout(() => {
          setCompletedGroups(prev => [...prev, group]);
          setTiles(prevTiles => prevTiles.map(tile => {
            if (group.words.includes(tile.word)) {
              return { ...tile, isSelected: false, group: group.theme };
            }
            return tile;
          }));

          // Show results after last group reveal
          if (index === remainingGroups.length - 1) {
            setJustEnded(true);
            setTimeout(() => {
              setShowResults(true);
            }, 1500);
          }
        }, index * 1500);
      });
    }, 2000);
  }, [completedGroups, tiles, puzzle, toast, mistakes]);

  useEffect(() => {
    if (puzzle && Array.isArray(puzzle.groups) && 
        completedGroups.length === puzzle.groups.length && 
        !gameFinished) {
      setTimeout(finishGame, 1000);
    }
  }, [completedGroups, puzzle, gameFinished, finishGame]);

  const handleShuffle = () => {
    const uncompletedTiles = tiles.filter(tile => !tile.group)
    const completedTiles = tiles.filter(tile => tile.group)
    setTiles([...completedTiles, ...shuffleArray(uncompletedTiles)])
  }

  const handleDeselectAll = () => {
    setTiles(tiles.map(tile => ({ ...tile, isSelected: false })))
  }

  const selectedCount = tiles.filter(tile => tile.isSelected).length

  const renderTiles = () => {
    const uncompletedTiles = tiles.filter(tile => !tile.group)
    
    return (
      <motion.div layout className="grid grid-cols-4 gap-1 sm:gap-2 mb-4 sm:mb-6 w-full">
        <AnimatePresence>
          {uncompletedTiles.map((tile, index) => (
            <motion.button
              key={tile.word}
              layout
              transition={{ duration: 0.5, ease: "easeInOut" }}
              onClick={() => handleTileClick(tiles.indexOf(tile))}
              className={`w-full h-20 sm:h-20 md:h-24 px-1 sm:px-2 py-0.5 sm:py-1 font-extrabold flex items-center justify-center text-center uppercase rounded-md transition-colors duration-200 ${
                tile.isSelected ? 'bg-gray-700 text-white' : 'bg-gray-100'
              }`}
              animate={tile.isAnimating ? { scale: [1, 1.1, 1] } : {}}
              whileTap={{ scale: 0.95 }}
            >
              <motion.span
                className={`
                  ${tile.word.length > 12 ? 'text-[8px] sm:text-xs md:text-sm' : 
                    tile.word.length > 8 ? 'text-[10px] sm:text-sm md:text-base' : 
                    'text-xs sm:text-base md:text-lg'}
                `}
                animate={tile.isShaking ? { x: [-5, 5, -5, 5, 0] } : {}}
                transition={{ duration: 0.5 }}
              >
                {tile.word.split(' ').map((word, i) => (
                  <React.Fragment key={i}>
                    {i > 0 && <br />}
                    {word}
                  </React.Fragment>
                ))}
              </motion.span>
            </motion.button>
          ))}
        </AnimatePresence>
      </motion.div>
    )
  }

  const renderCompletedGroups = () => {
    return completedGroups.map((group, groupIndex) => (
      <motion.div
        key={groupIndex}
        initial={{ scale: 1 }}
        animate={justEnded ? { scale: [1, 1.2, 1] } : {}}
        transition={{ delay: 0.2, duration: 0.5 }}
        className={`mb-1 sm:mb-2 p-2 rounded-md ${getGroupColor(group.color)} h-20 sm:h-20 flex flex-col justify-center`}
      >
        <h3 className="font-extrabold text-center mb-1 text-xs sm:text-sm uppercase">
          {group.theme}
        </h3>
        <p className={`text-center uppercase font-medium
          ${group.words.join(', ').length > 50 ? 'text-[10px] sm:text-sm' : 
            group.words.join(', ').length > 40 ? 'text-xs sm:text-base' : 
            'text-sm sm:text-lg'}`}>
          {group.words.join(', ')}
        </p>
      </motion.div>
    ))
  }

  const getGroupColor = (color: string) => {
    switch (color) {
      case 'bg-yellow-200':
        return 'bg-yellow-300';
      case 'bg-green-200':
        return 'bg-green-500';
      case 'bg-blue-200':
        return 'bg-blue-500';
      case 'bg-purple-200':
        return 'bg-purple-500';
      default:
        return color;
    }
  }

  const handleBackToPuzzle = () => {
    setShowResults(false);
    setJustEnded(false); // Reset this when going back to the puzzle
  }

  const handleShareResults = () => {
    const resultsText = `NBA Connections
Puzzle #${puzzle?.puzzle_id}
${guesses.map(guess => 
  guess.selectedWords.map(word => {
    const correctGroup = puzzle?.groups.find(group => group.words.includes(word));
    return correctGroup?.emoji || '⬜';
  }).join('')
).join('\n')}`;

    navigator.clipboard.writeText(resultsText).then(() => {
      toast({
        description: "Results copied to clipboard!",
        duration: 2000,
      });
    });
  }

  const renderResults = () => {
    return (
      <div className="fixed inset-0 bg-white z-50 overflow-auto">
        <div className="flex justify-end mt-2 mr-2">
          <button
            onClick={handleBackToPuzzle}
            className="flex items-center text-gray-600 hover:text-gray-800"
          >
            Back to puzzle
            <XIcon className="w-5 h-5 ml-1" />
          </button>
        </div>
        <div className="mt-8 flex flex-col items-center">
          <h2 className="text-2xl font-bold mb-2">
            {mistakes > 0 && completedGroups.length === puzzle?.groups.length ? 'Slam Dunk!' : 'Airball!'}
          </h2>
          {mistakes === 0 && (
            <p className="text-lg mb-2">See you tomorrow for a rematch</p>
          )}
          <p className="text-lg mb-2">NBA Connections #{puzzle?.puzzle_id}</p>
          <div className="flex flex-col items-center gap-1 mb-4">
            {guesses.map((guess, index) => (
              <div key={index} className="flex gap-1">
                {guess.selectedWords.map((word, i) => {
                  const correctGroup = puzzle?.groups.find(group => group.words.includes(word));
                  return (
                    <div
                      key={i}
                      className={`w-6 h-6 sm:w-8 sm:h-8 ${getResultColor(correctGroup?.color)} rounded-sm`}
                    />
                  );
                })}
              </div>
            ))}
          </div>
          <Button 
            className="text-xs bg-white text-black border border-black hover:bg-gray-100 rounded-full px-3 py-1 mb-2" 
            onClick={handleShareResults}
          >
            Share Your Results
          </Button>
        </div>
      </div>
    )
  }

  const getResultColor = (color: string | undefined) => {
    switch (color) {
      case 'bg-yellow-200':
        return 'bg-yellow-300';
      case 'bg-green-200':
        return 'bg-green-500';
      case 'bg-blue-200':
        return 'bg-blue-500';
      case 'bg-purple-200':
        return 'bg-purple-500';
      default:
        return 'bg-gray-300'; // for incorrect guesses
    }
  }

  const getCurrentDate = () => {
    const options: Intl.DateTimeFormatOptions = { month: 'long', day: 'numeric', year: 'numeric' };
    return new Date().toLocaleDateString('en-US', options);
  }

  const handleStartGame = () => {
    if (gamePhase === 'ready') {
      // Reset all tiles to unselected state before starting the game
      setTiles(prevTiles => prevTiles.map(tile => ({ ...tile, isSelected: false })));
      setGamePhase('playing');
    }
  }

  const renderHeader = () => (
    <header className="w-full p-4 flex justify-between items-center bg-gray-100">
      <h1 className="text-xl font-bold">NBA C🏀nnecti🏀ns</h1>
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <Button variant="ghost" size="icon">
            <Menu className="h-6 w-6" />
          </Button>
        </DropdownMenuTrigger>
        <DropdownMenuContent className="bg-white shadow-lg rounded-md">
          <DropdownMenuItem onSelect={() => setShowHowToPlay(true)}>
            How to Play
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => window.location.href = 'mailto:mannelly.john@gmail.com?subject=NBA Connections Feedback'}>
            Feedback
            <ArrowUpRight className="h-4 w-4 ml-2" />
          </DropdownMenuItem>
          <DropdownMenuItem onSelect={() => window.location.href = 'mailto:mannelly.john@gmail.com?subject=NBA Connections Puzzle Submission'}>
            Submit a Puzzle
            <ArrowUpRight className="h-4 w-4 ml-2" />
          </DropdownMenuItem>
        </DropdownMenuContent>
      </DropdownMenu>
    </header>
  )

  const renderHowToPlay = () => (
    <div className="fixed inset-0 bg-white z-50 overflow-auto">
      <div className="max-w-2xl mx-auto p-6">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-2xl font-bold">How to Play</h2>
          <button onClick={() => setShowHowToPlay(false)} className="text-gray-500 hover:text-gray-700">
            <X className="h-6 w-6" />
          </button>
        </div>
        <div className="space-y-4">
          <p>Find groups of four players that share something in common.</p>
          <ul className="list-disc pl-5 space-y-2">
            <li>Select four players and tap 'Shoot!' To check if your guess is correct.</li>
            <li>Find the groups without making 4 mistakes!</li>
          </ul>
          <h3 className="font-bold mt-4">Category Examples</h3>
          <ul className="list-disc pl-5 space-y-2">
            <li>Players that wore the number 3: Allen Iverson, Chris Paul, Dennis Johnson, Dražen Petrovi</li>
            <li>Players drafted in 2003: Lebron James, Chris Bosh, Dwayne Wade, Carmelo Anthony</li>
          </ul>
          <p>Each puzzle has exactly one solution and is meant to be tricky by having players that could fit into multiple categories.</p>
          <p>Each group is assigned a color, which will be revealed as you solve:</p>
          <div className="flex items-center space-x-2 mt-2">
            <div className="w-4 h-4 bg-yellow-300"></div>
            <span>Straightforward</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-green-500"></div>
            <span>Moderate</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-blue-500"></div>
            <span>Challenging</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-4 h-4 bg-purple-500"></div>
            <span>Tricky</span>
          </div>
        </div>
      </div>
    </div>
  )

  if (gamePhase === 'loading' || gamePhase === 'ready') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100 p-2">
        <div className="text-center">
          <BasketballIcon className="w-20 h-20 text-gray-700 mx-auto mb-4" />
          <h1 className="text-3xl font-black text-gray-800 mb-2">NBA Connections</h1>
          <p className="text-lg text-gray-600 mb-6 max-w-[20ch] min-w-[15ch] mx-auto leading-tight sm:max-w-none sm:w-auto">
            Group NBA players that share a common thread.
          </p>
          {gamePhase === 'loading' ? (
            <p className="text-lg text-gray-600 mb-4">Loading puzzle...</p>
          ) : (
            <Button 
              onClick={handleStartGame}
              className="bg-black hover:bg-gray-800 text-white font-bold py-2 px-6 rounded-full text-lg transition-all duration-200 ease-in-out transform hover:scale-105 mb-4 w-36"
            >
              Tip Off
            </Button>
          )}
          <p className="text-sm text-gray-600">{getCurrentDate()}</p>
          {puzzle && (
            <>
              <p className="text-sm text-gray-600">No. {puzzle.puzzle_id}</p>
              <p className="text-sm text-gray-600">Edited by {puzzle.author}</p>
            </>
          )}
        </div>
      </div>
    );
  }

  if (gamePhase !== 'playing') {
    return null; // or some loading indicator if needed
  }

  return (
    <div className="flex flex-col min-h-screen bg-white">
      {showConfetti && confetti({
        particleCount: 200,
        spread: 70,
        origin: { y: 0.6 }
      })}
      {renderHeader()}
      <div className="p-1 sm:p-2 flex-grow flex flex-col items-center w-full">
        <div className="w-full max-w-3xl">
          <div className="mb-4 sm:mb-6 flex justify-between items-baseline">
            {/* Remove the existing title here */}
          </div>
          {showResults ? (
            <div className="mb-4 flex-grow flex items-center justify-center">
              <div className="bg-white p-4 rounded-lg shadow-lg w-full">
                {renderResults()}
              </div>
            </div>
          ) : (
            <div className="flex-grow flex flex-col justify-center">
              <div className="bg-[#E87503] rounded-t-lg mb-0.5 px-4 py-0.5">
                <h2 className="text-xs font-semibold text-center text-white">TODAY'S THEME</h2>
              </div>
              <div className="bg-white rounded-b-lg mb-2 px-4 py-1 shadow-sm">
                <h3 className="text-lg font-extrabold text-center text-gray-800">Jersey Numbers</h3>
              </div>
              <div className="flex flex-col">
                {renderCompletedGroups()}
                {renderTiles()}
                {completedGroups.length !== puzzle?.groups.length && (
                  <div className="flex items-center justify-center space-x-1 my-3 sm:my-4">
                    <span className="text-xs">Timeouts Remaining:</span>
                    {[...Array(4)].map((_, i) => (
                      <div key={i} className={`w-2 h-2 rounded-full ${i < mistakes ? 'bg-gray-600' : 'bg-gray-300'}`} />
                    ))}
                  </div>
                )}
                {completedGroups.length === puzzle?.groups.length ? (
                  <div className="flex justify-center mt-3 sm:mt-4">
                    <Button 
                      className="text-xs bg-black text-white hover:bg-gray-800 rounded-full px-6 py-2" 
                      onClick={() => setShowResults(true)}
                    >
                      View Box Score
                    </Button>
                  </div>
                ) : (
                  <div className="flex justify-center space-x-2 mt-3 sm:mt-4">
                    <Button 
                      onClick={handleShuffle} 
                      className="text-xs bg-white text-black border border-black hover:bg-gray-100 rounded-full px-3 py-1"
                    >
                      Shuffle
                    </Button>
                    <Button 
                      variant="outline" 
                      onClick={handleDeselectAll}
                      disabled={selectedCount === 0}
                      className={`text-xs border rounded-full px-3 py-1 ${
                        selectedCount > 0 
                          ? 'bg-white text-black border-black hover:bg-gray-100' 
                          : 'bg-gray-100 text-gray-400 border-gray-300'
                      }`}
                    >
                      Subsitute All
                    </Button>
                    <Button 
                      onClick={handleSubmit}
                      disabled={
                        selectedCount !== 4 || 
                        guesses.some(guess => 
                          JSON.stringify(guess.selectedWords.sort()) === JSON.stringify(tiles.filter(tile => tile.isSelected).map(tile => tile.word).sort())
                        )
                      }
                      className={`text-xs rounded-full px-3 py-1 ${
                        selectedCount === 4 && !guesses.some(guess => 
                          JSON.stringify(guess.selectedWords.sort()) === JSON.stringify(tiles.filter(tile => tile.isSelected).map(tile => tile.word).sort())
                        )
                          ? 'bg-black text-white hover:bg-gray-800' 
                          : 'bg-gray-100 text-gray-400 border border-gray-300'
                      }`}
                    >
                      Shoot!
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
      <footer className="w-full text-center py-2 text-xs text-gray-500 sticky bottom-0 bg-white">
        Made by <Link href="https://x.com/learnwithjabe" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">@learnwithjabe</Link>
      </footer>
      <Toaster />
      {showHowToPlay && renderHowToPlay()}
      {showResults && renderResults()} {/* Moved outside main content to overlay */}
    </div>
  )
}
