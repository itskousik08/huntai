const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');

const app = express();
app.use(cors());

const server = http.createServer(app);
const io = new Server(server, {
    cors: { origin: '*', methods: ["GET", "POST"] }
});

// Rooms storage in-memory
let rooms = {};

io.on('connection', (socket) => {
    console.log('User Connected:', socket.id);

    // Create Room Logic
    socket.on('create-room', ({ roomId, name, limit, duration }) => {
        const expiryTime = Date.now() + duration;
        
        rooms[roomId] = {
            users: [socket.id],
            limit: limit || 2,
            expires: expiryTime,
            creator: socket.id
        };

        socket.join(roomId);
        socket.emit('room-created', { roomId, expiryTime });

        // Auto-delete room after duration
        setTimeout(() => {
            if (rooms[roomId]) {
                io.to(roomId).emit('expired', 'Room has expired and is now closed.');
                delete rooms[roomId];
            }
        }, duration);
    });

    // Join Room Logic
    socket.on('join-room', ({ roomId, name }) => {
        const room = rooms[roomId];

        if (!room) {
            return socket.emit('error-msg', 'Room not found or expired.');
        }
        if (Date.now() > room.expires) {
            delete rooms[roomId];
            return socket.emit('error-msg', 'Room already expired.');
        }
        if (room.users.length >= room.limit) {
            return socket.emit('error-msg', 'Room is full.');
        }

        room.users.push(socket.id);
        socket.join(roomId);
        
        // Notify other users in the room
        socket.to(roomId).emit('user-joined', { name, count: room.users.length });
        socket.emit('joined-success', { roomId });
    });

    // Message Logic
    socket.on('send-message', ({ roomId, msg, sender }) => {
        if (rooms[roomId]) {
            socket.to(roomId).emit('receive-message', { msg, sender });
        }
    });

    // Handle Disconnect
    socket.on('disconnect', () => {
        for (let rid in rooms) {
            rooms[rid].users = rooms[rid].users.filter(id => id !== socket.id);
            if (rooms[rid].users.length === 0) {
                delete rooms[rid];
            }
        }
        console.log('User Disconnected:', socket.id);
    });
});

const PORT = process.env.PORT || 3000;
server.listen(PORT, () => console.log(`Server running on port ${PORT}`));
