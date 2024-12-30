import React, { useState, useEffect } from 'react';
import { Sparkles, Flame, Droplets, Wind, Mountain, Sun, Moon } from 'lucide-react';

const MagicForestMatch = () => {
  const BOARD_SIZE = 8;
  const RUNE_TYPES = [
    { type: 'fire', icon: Flame, color: 'text-red-500', bg: 'bg-red-100' },
    { type: 'water', icon: Droplets, color: 'text-blue-500', bg: 'bg-blue-100' },
    { type: 'wind', icon: Wind, color: 'text-green-500', bg: 'bg-green-100' },
    { type: 'earth', icon: Mountain, color: 'text-amber-700', bg: 'bg-amber-100' },
    { type: 'light', icon: Sun, color: 'text-yellow-500', bg: 'bg-yellow-100' },
    { type: 'shadow', icon: Moon, color: 'text-purple-500', bg: 'bg-purple-100' }
  ];

  const [board, setBoard] = useState([]);
  const [score, setScore] = useState(0);
  const [selectedTile, setSelectedTile] = useState(null);
  const [matches, setMatches] = useState([]);
  const [isAnimating, setIsAnimating] = useState(false);
  const [gameLevel, setGameLevel] = useState(1);
  const [movesLeft, setMovesLeft] = useState(20);

  useEffect(() => {
    initializeBoard();
  }, []);

  const initializeBoard = () => {
    const newBoard = Array(BOARD_SIZE).fill(0).map(() =>
      Array(BOARD_SIZE).fill(0).map(() =>
        RUNE_TYPES[Math.floor(Math.random() * RUNE_TYPES.length)]
      )
    );
    setBoard(newBoard);
    setScore(0);
    setMovesLeft(20);
    setGameLevel(1);
  };

  const isAdjacent = (pos1, pos2) => {
    if (!pos1 || !pos2) return false;
    const rowDiff = Math.abs(pos1.row - pos2.row);
    const colDiff = Math.abs(pos1.col - pos2.col);
    return (rowDiff === 1 && colDiff === 0) || (rowDiff === 0 && colDiff === 1);
  };

  const swapTiles = (pos1, pos2) => {
    if (isAnimating || movesLeft <= 0) return;
    
    const newBoard = [...board];
    const temp = newBoard[pos1.row][pos1.col];
    newBoard[pos1.row][pos1.col] = newBoard[pos2.row][pos2.col];
    newBoard[pos2.row][pos2.col] = temp;
    
    setBoard(newBoard);
    setMovesLeft(prev => prev - 1);
    setTimeout(() => checkMatches(newBoard), 300);
  };

  const handleTileClick = (row, col) => {
    if (isAnimating || movesLeft <= 0) return;
    
    const clickedTile = { row, col };
    
    if (!selectedTile) {
      setSelectedTile(clickedTile);
    } else {
      if (isAdjacent(selectedTile, clickedTile)) {
        swapTiles(selectedTile, clickedTile);
      }
      setSelectedTile(null);
    }
  };

  const checkMatches = (currentBoard) => {
    setIsAnimating(true);
    const newMatches = new Set();
    
    // Check horizontal matches
    for (let row = 0; row < BOARD_SIZE; row++) {
      for (let col = 0; col < BOARD_SIZE - 2; col++) {
        if (
          currentBoard[row][col].type === currentBoard[row][col + 1].type &&
          currentBoard[row][col].type === currentBoard[row][col + 2].type
        ) {
          newMatches.add(`${row},${col}`);
          newMatches.add(`${row},${col + 1}`);
          newMatches.add(`${row},${col + 2}`);
        }
      }
    }
    
    // Check vertical matches
    for (let row = 0; row < BOARD_SIZE - 2; row++) {
      for (let col = 0; col < BOARD_SIZE; col++) {
        if (
          currentBoard[row][col].type === currentBoard[row + 1][col].type &&
          currentBoard[row][col].type === currentBoard[row + 2][col].type
        ) {
          newMatches.add(`${row},${col}`);
          newMatches.add(`${row + 1},${col}`);
          newMatches.add(`${row + 2},${col}`);
        }
      }
    }

    if (newMatches.size > 0) {
      setScore(prev => prev + newMatches.size * 50);
      setMatches(Array.from(newMatches));
      setTimeout(() => {
        removeMatches(currentBoard, newMatches);
      }, 500);
    } else {
      setIsAnimating(false);
    }
  };

  const removeMatches = (currentBoard, matchSet) => {
    const newBoard = [...currentBoard];
    
    matchSet.forEach(match => {
      const [row, col] = match.split(',').map(Number);
      newBoard[row][col] = null;
    });
    
    setBoard(newBoard);
    setTimeout(() => {
      fillEmptySpaces(newBoard);
    }, 300);
  };

  const fillEmptySpaces = (currentBoard) => {
    const newBoard = [...currentBoard];
    
    for (let col = 0; col < BOARD_SIZE; col++) {
      let emptySpaces = 0;
      
      // Move runes down
      for (let row = BOARD_SIZE - 1; row >= 0; row--) {
        if (!newBoard[row][col]) {
          emptySpaces++;
        } else if (emptySpaces > 0) {
          newBoard[row + emptySpaces][col] = newBoard[row][col];
          newBoard[row][col] = null;
        }
      }
      
      // Fill empty spaces with new runes
      for (let row = 0; row < emptySpaces; row++) {
        newBoard[row][col] = RUNE_TYPES[Math.floor(Math.random() * RUNE_TYPES.length)];
      }
    }
    
    setBoard(newBoard);
    setMatches([]);
    setTimeout(() => {
      checkMatches(newBoard);
    }, 300);
  };

  const renderRune = (rune, isMatched) => {
    if (!rune) return null;
    const IconComponent = rune.icon;
    return (
      <div className={`relative ${rune.bg} rounded-lg w-full h-full flex items-center justify-center 
                      ${isMatched ? 'animate-pulse' : ''}`}>
        <IconComponent className={`${rune.color} w-8 h-8`} />
        {isMatched && <Sparkles className="absolute text-yellow-400 w-6 h-6" />}
      </div>
    );
  };

  return (
    <div className="flex flex-col items-center gap-6 p-6 bg-gradient-to-b from-green-50 to-blue-50 min-h-screen">
      <div className="text-3xl font-bold text-green-800">魔法森林探险</div>
      
      <div className="flex gap-8 text-xl">
        <div className="bg-white px-4 py-2 rounded-lg shadow">
          <span className="font-bold text-purple-600">分数:</span> {score}
        </div>
        <div className="bg-white px-4 py-2 rounded-lg shadow">
          <span className="font-bold text-blue-600">关卡:</span> {gameLevel}
        </div>
        <div className="bg-white px-4 py-2 rounded-lg shadow">
          <span className="font-bold text-red-600">剩余步数:</span> {movesLeft}
        </div>
      </div>

      <div className="grid gap-1 p-4 bg-white/80 rounded-xl shadow-xl backdrop-blur-sm"
           style={{ gridTemplateColumns: `repeat(${BOARD_SIZE}, 1fr)` }}>
        {board.map((row, rowIndex) => (
          row.map((rune, colIndex) => (
            <button
              key={`${rowIndex}-${colIndex}`}
              className={`w-16 h-16 rounded-lg transition-all duration-200 ${
                selectedTile?.row === rowIndex && selectedTile?.col === colIndex
                  ? 'ring-4 ring-yellow-400'
                  : 'hover:ring-2 hover:ring-blue-300'
              }`}
              onClick={() => handleTileClick(rowIndex, colIndex)}
              disabled={isAnimating || movesLeft <= 0}
            >
              {renderRune(rune, matches.includes(`${rowIndex},${colIndex}`))}
            </button>
          ))
        ))}
      </div>

      {movesLeft <= 0 && (
        <div className="text-2xl font-bold text-red-600">游戏结束!</div>
      )}

      <button 
        className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 
                   transition-colors duration-200 font-bold shadow-lg"
        onClick={initializeBoard}
      >
        重新开始
      </button>
    </div>
  );
};

export default MagicForestMatch;