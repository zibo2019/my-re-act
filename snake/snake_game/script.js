const canvas = document.getElementById('gameCanvas');
const context = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const gameOverEl = document.getElementById('gameOver');
const restartBtn = document.getElementById('restartBtn');

const gridSize = 20;
const canvasSize = 400;
canvas.width = canvasSize;
canvas.height = canvasSize;

let snake, food, score, direction, gameInterval, changingDirection;

function startGame() {
    snake = [{x: 10 * gridSize, y: 10 * gridSize}];
    food = randomFoodPosition();
    score = 0;
    direction = 'right';
    changingDirection = false;
    scoreEl.innerText = score;
    gameOverEl.classList.add('hidden');

    if (gameInterval) clearInterval(gameInterval);
    gameInterval = setInterval(gameLoop, 120);
}

function randomFoodPosition() {
    let x = Math.floor(Math.random() * (canvas.width / gridSize)) * gridSize;
    let y = Math.floor(Math.random() * (canvas.height / gridSize)) * gridSize;
    return {x, y};
}

function gameLoop() {
    if (update()) {
        draw();
    } else {
        endGame();
    }
}

function update() {
    changingDirection = false;
    const head = {...snake[0]};

    switch(direction) {
        case 'right': head.x += gridSize; break;
        case 'left': head.x -= gridSize; break;
        case 'up': head.y -= gridSize; break;
        case 'down': head.y += gridSize; break;
    }

    // Check for wall collision
    if (head.x < 0 || head.x >= canvas.width || head.y < 0 || head.y >= canvas.height) {
        return false;
    }

    // Check for self collision
    for (let i = 1; i < snake.length; i++) {
        if (head.x === snake[i].x && head.y === snake[i].y) {
            return false;
        }
    }

    snake.unshift(head);

    if (head.x === food.x && head.y === food.y) {
        score++;
        scoreEl.innerText = score;
        food = randomFoodPosition();
    } else {
        snake.pop();
    }

    return true;
}

function draw() {
    context.clearRect(0, 0, canvas.width, canvas.height);

    // Draw snake
    snake.forEach((part, index) => {
        context.fillStyle = index === 0 ? '#0f0' : '#0a0';
        context.fillRect(part.x, part.y, gridSize, gridSize);
        context.strokeStyle = '#000';
        context.strokeRect(part.x, part.y, gridSize, gridSize);
    });

    // Draw food
    context.fillStyle = 'red';
    context.fillRect(food.x, food.y, gridSize, gridSize);
    context.strokeStyle = '#400';
    context.strokeRect(food.x, food.y, gridSize, gridSize);
}

function changeDirection(e) {
    if (changingDirection) return;
    changingDirection = true;

    const key = e.code;
    const goingUp = direction === 'up';
    const goingDown = direction === 'down';
    const goingLeft = direction === 'left';
    const goingRight = direction === 'right';

    if (key === 'ArrowUp' && !goingDown) {
        direction = 'up';
    } else if (key === 'ArrowDown' && !goingUp) {
        direction = 'down';
    } else if (key === 'ArrowLeft' && !goingRight) {
        direction = 'left';
    } else if (key === 'ArrowRight' && !goingLeft) {
        direction = 'right';
    }
}

function endGame() {
    clearInterval(gameInterval);
    gameOverEl.classList.remove('hidden');
}

window.addEventListener('keydown', changeDirection);
restartBtn.addEventListener('click', startGame);

startGame(); // Initial start
