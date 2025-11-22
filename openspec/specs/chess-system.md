# Chess System Specification: Robot Chess Player

**Version:** 1.0.0
**Last Updated:** 2025-11-22
**Status:** Active

## Overview

This specification defines the chess-playing capabilities of the robot simulation system. It enables LLM agents to play chess by controlling a robotic arm to move physical chess pieces on a virtual board within the Unity simulation.

---

## Requirements

### Requirement: CHESS-001 - Board Representation
The system SHALL maintain an accurate representation of the chess board state.

#### Scenario: Initial Board Setup
- WHEN a new chess game is started
- THEN the system SHALL place all 32 pieces in their standard starting positions
- AND update the internal board state representation

#### Scenario: Board State Query
- WHEN an LLM queries the board state
- THEN the system SHALL return the position of all pieces
- AND indicate captured pieces and whose turn it is

#### Scenario: Board Coordinate System
- WHEN referencing board positions
- THEN the system SHALL use standard algebraic notation (a1-h8)
- AND support conversion to/from Cartesian coordinates

---

### Requirement: CHESS-002 - Piece Recognition
The system SHALL identify and track all chess pieces on the board.

#### Scenario: Piece Identification
- WHEN a piece position is queried
- THEN the system SHALL return the piece type (King, Queen, Rook, Bishop, Knight, Pawn)
- AND the piece color (White, Black)

#### Scenario: Piece Location Tracking
- WHEN a piece is moved
- THEN the system SHALL update the piece's tracked position
- AND maintain history of all moves

---

### Requirement: CHESS-003 - Move Execution
The system SHALL execute chess moves using the robotic arm.

#### Scenario: Standard Move
- WHEN an LLM commands a standard move (e.g., "e2 to e4")
- THEN the robot SHALL:
  1. Move to the source square
  2. Grip the piece
  3. Lift the piece
  4. Move to the destination square
  5. Lower the piece
  6. Release the gripper
- AND update the board state

#### Scenario: Capture Move
- WHEN an LLM commands a capture move
- THEN the robot SHALL:
  1. Move to the destination square
  2. Grip the captured piece
  3. Move to the capture zone
  4. Release the captured piece
  5. Return to execute the standard move sequence
- AND update both pieces' states

#### Scenario: Castling Move
- WHEN an LLM commands a castling move
- THEN the robot SHALL move the King first
- THEN move the Rook to its new position
- AND update both pieces' board positions

#### Scenario: En Passant Move
- WHEN an LLM commands an en passant capture
- THEN the robot SHALL move the pawn diagonally
- AND remove the captured pawn from its original square
- AND update the board state correctly

#### Scenario: Pawn Promotion
- WHEN a pawn reaches the back rank
- THEN the system SHALL query the LLM for promotion choice
- AND replace the pawn with the chosen piece type

---

### Requirement: CHESS-004 - Move Validation
The system SHALL validate chess moves before execution.

#### Scenario: Legal Move Check
- WHEN an LLM proposes a move
- THEN the system SHALL verify the move is legal according to chess rules
- AND reject illegal moves with an explanation

#### Scenario: Check Detection
- WHEN a move would put the king in check
- THEN the system SHALL detect and report the check condition
- AND prevent illegal moves that leave the king in check

#### Scenario: Checkmate Detection
- WHEN no legal moves are available and the king is in check
- THEN the system SHALL declare checkmate
- AND end the game

#### Scenario: Stalemate Detection
- WHEN no legal moves are available and the king is not in check
- THEN the system SHALL declare stalemate
- AND end the game as a draw

---

### Requirement: CHESS-005 - Game Management
The system SHALL manage chess game sessions.

#### Scenario: New Game
- WHEN an LLM sends a `new_game` command
- THEN the system SHALL reset all pieces to starting positions
- AND clear the move history
- AND set White to move first

#### Scenario: Game State Query
- WHEN an LLM queries the game state
- THEN the system SHALL return:
  - Current board position (FEN notation)
  - Move history (algebraic notation)
  - Current player's turn
  - Game status (ongoing, check, checkmate, stalemate, draw)

#### Scenario: Undo Move
- WHEN an LLM sends an `undo` command
- THEN the robot SHALL physically restore the previous position
- AND update the board state accordingly

---

## Chess Command Reference

### Game Commands

| Command | Parameters | Description |
|---------|------------|-------------|
| `new_game` | [fen_position] | Start new game, optionally from FEN |
| `make_move` | from, to, [promotion] | Execute a chess move |
| `get_board` | - | Get current board state |
| `get_legal_moves` | [square] | Get legal moves (optionally for specific piece) |
| `undo_move` | - | Undo the last move |
| `resign` | - | Resign the current game |

### Query Commands

| Command | Returns | Description |
|---------|---------|-------------|
| `get_fen` | FEN string | Current position in FEN notation |
| `get_pgn` | PGN string | Game in PGN format |
| `get_piece_at` | piece info | Piece at specified square |
| `is_check` | boolean | Whether current player is in check |
| `is_game_over` | boolean, reason | Whether game has ended |

---

## Board Layout

```
    a   b   c   d   e   f   g   h
  +---+---+---+---+---+---+---+---+
8 | r | n | b | q | k | b | n | r | 8  (Black)
  +---+---+---+---+---+---+---+---+
7 | p | p | p | p | p | p | p | p | 7
  +---+---+---+---+---+---+---+---+
6 |   |   |   |   |   |   |   |   | 6
  +---+---+---+---+---+---+---+---+
5 |   |   |   |   |   |   |   |   | 5
  +---+---+---+---+---+---+---+---+
4 |   |   |   |   |   |   |   |   | 4
  +---+---+---+---+---+---+---+---+
3 |   |   |   |   |   |   |   |   | 3
  +---+---+---+---+---+---+---+---+
2 | P | P | P | P | P | P | P | P | 2
  +---+---+---+---+---+---+---+---+
1 | R | N | B | Q | K | B | N | R | 1  (White)
  +---+---+---+---+---+---+---+---+
    a   b   c   d   e   f   g   h

Legend: K=King, Q=Queen, R=Rook, B=Bishop, N=Knight, P=Pawn
        Uppercase=White, Lowercase=Black
```

---

## Physical Piece Specifications

| Piece | Prefab | Grip Height | Notes |
|-------|--------|-------------|-------|
| King | Chess King White/Black | 80mm | Tallest piece |
| Queen | Chess Queen White/Black | 70mm | |
| Rook | Chess Rook White/Black | 45mm | |
| Bishop | Chess Bishop White/Black | 60mm | |
| Knight | Chess Knight White/Black | 55mm | Asymmetric grip |
| Pawn | Chess Pawn White/Black | 35mm | Most common |

---

## Response Examples

### Successful Move
```json
{
  "command": "make_move",
  "status": "success",
  "data": {
    "move": "e2e4",
    "notation": "e4",
    "piece": "Pawn",
    "captured": null,
    "is_check": false,
    "is_checkmate": false,
    "fen": "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
  }
}
```

### Capture Move
```json
{
  "command": "make_move",
  "status": "success",
  "data": {
    "move": "d4e5",
    "notation": "dxe5",
    "piece": "Pawn",
    "captured": "Pawn",
    "is_check": false,
    "is_checkmate": false
  }
}
```

### Illegal Move Error
```json
{
  "command": "make_move",
  "status": "error",
  "error": {
    "code": "ILLEGAL_MOVE",
    "message": "Move e1e3 is not legal. King cannot move 2 squares."
  }
}
```

---

## Related Specifications

- [system.md](system.md) - Core system specification
- [robot-interface.md](robot-interface.md) - Robot control interface
- [communication.md](communication.md) - Communication protocol
