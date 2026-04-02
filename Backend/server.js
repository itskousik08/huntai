const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors()); // Allow all origins

const server = http.createServer(app);
const io = new Server(server, {
    cors: {
        origin: "*", // Essential for Render deployment
        methods: ["GET", "POST"]
    }
});

let rooms = {};

io.on('connection', (socket) => {
    console.log('User connected:', socket.id);

    // Create Room
    socket.on('create-room', ({ roomId, name, limit, duration }) => {
        rooms[roomId] = {
            users: [socket.id],
            limit: limit || 2,
            expires: Date.now() + duration
        };
        socket.join(roomId);
        console.log(`Room ${roomId} created by ${name}`);
        
        // Auto-delete room
        setTimeout(() => {
            if (rooms[roomId]) {
                io.to(roomId).emit('expired');
                delete rooms[roomId];
            }
        }, duration);
    });

    // Join Room
    socket.on('join-room', ({ roomId, name }) => {
        const room = rooms[roomId];
        if (room && room.users.length < room.limit) {
            room.users.push(socket.id);
            socket.join(roomId);
            socket.to(roomId).emit('user-joined', name);
            socket.emit('joined-success', roomId);
            console.log(`${name} joined room ${roomId}`);
        } else {
            socket.emit('error-msg', room ? 'Room is full!' : 'Room not found!');
        }
    });

    // Message Handling (The Fix)
    socket.on('message', ({ roomId, msg, sender }) => {
        // Broadcast to everyone in the room EXCEPT the sender
        socket.to(roomId).emit('message', { msg, sender });
    });

    socket.on('disconnect', () => {
        for (let id in rooms) {
            rooms[id].users = rooms[id].users.filter(u => u !== socket.id);
            if (rooms[id].users.length === 0) delete rooms[id];
        }
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`Server running on port ${PORT}`));
