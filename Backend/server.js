/**
 * ╔══════════════════════════════════════════════╗
 * ║  HUNT AI — Signaling & Room Management Server ║
 * ║  Built by axeroai                            ║
 * ╚══════════════════════════════════════════════╝
 *
 * Stack   : Node.js + Express + Socket.io
 * Storage : In-memory only (no database, no message persistence)
 * Role    : WebRTC signaling + room lifecycle + message relay
 *
 * Deploy on Render:
 *   Root Dir     → Backend
 *   Build Cmd    → npm install
 *   Start Cmd    → node server.js
 *   Env Var      → PORT (auto-set by Render)
 */

'use strict';

const express = require('express');
const http    = require('http');
const { Server } = require('socket.io');
const crypto  = require('crypto');

const app    = express();
const server = http.createServer(app);
const PORT   = process.env.PORT || 3000;

// ─── CORS: allow all origins so static frontends can connect ───────────────
const io = new Server(server, {
  cors: {
    origin : '*',
    methods: ['GET', 'POST'],
  },
  pingTimeout : 60000,
  pingInterval: 25000,
});

// ─── In-memory room registry ────────────────────────────────────────────────
// Map<roomId:string, Room>
const rooms = new Map();

/**
 * Room shape:
 * {
 *   id            : string           — 6-digit room ID
 *   users         : Array<{id,name}> — connected socket users
 *   callers       : Set<socketId>    — users currently in voice call
 *   limit         : number           — max concurrent users
 *   createdAt     : number           — unix ms
 *   expiresAt     : number           — unix ms
 *   expiredNotify : boolean          — have we sent the expiry event yet?
 * }
 */

// ─── Helpers ────────────────────────────────────────────────────────────────

function generateRoomId () {
  let id, tries = 0;
  do {
    id = String(Math.floor(100000 + Math.random() * 900000));
    if (++tries > 9999) throw new Error('ID space exhausted');
  } while (rooms.has(id));
  return id;
}

const isExpired = room => Date.now() >= room.expiresAt;
const isFull    = room => room.users.length >= room.limit;

// ─── Periodic room cleanup (every 20 s) ─────────────────────────────────────
setInterval(() => {
  const now = Date.now();
  for (const [roomId, room] of rooms) {

    // First-time expiry notification
    if (now >= room.expiresAt && !room.expiredNotify) {
      io.to(roomId).emit('room-expired', {
        message: 'This room has expired. No new users can join, but you may keep chatting.',
      });
      room.expiredNotify = true;
    }

    // Hard-delete: expired + empty + grace period (30 min)
    if (now >= room.expiresAt + 30 * 60_000 && room.users.length === 0) {
      rooms.delete(roomId);
      console.log(`[GC] Room ${roomId} deleted.`);
    }
  }
}, 20_000);

// ─── HTTP routes ─────────────────────────────────────────────────────────────
app.use(express.json());

app.get('/', (_req, res) =>
  res.json({ app: 'HUNT AI', status: 'running', rooms: rooms.size, ts: new Date().toISOString() })
);

app.get('/health', (_req, res) =>
  res.json({ status: 'healthy', rooms: rooms.size, uptime: process.uptime() })
);

// ─── Socket.io ───────────────────────────────────────────────────────────────
io.on('connection', socket => {
  console.log(`[+] ${socket.id} connected`);

  let currentRoomId = null;
  let currentUser   = null;

  // ── CREATE ROOM ────────────────────────────────────────────────────────────
  socket.on('create-room', ({ name, limit, duration, durationUnit }) => {
    try {
      name = (name || '').trim();
      if (!name) return emit_err('INVALID_NAME', 'Please enter your name.');

      const userLimit = parseInt(limit);
      if (isNaN(userLimit) || userLimit < 2 || userLimit > 10)
        return emit_err('INVALID_LIMIT', 'User limit must be 2–10.');

      const dur = parseInt(duration);
      if (isNaN(dur) || dur < 1)
        return emit_err('INVALID_DURATION', 'Enter a valid duration.');

      const durMs     = durationUnit === 'minutes' ? dur * 60_000 : dur * 1_000;
      const roomId    = generateRoomId();
      const user      = { id: socket.id, name };

      const room = {
        id           : roomId,
        users        : [user],
        callers      : new Set(),
        limit        : userLimit,
        createdAt    : Date.now(),
        expiresAt    : Date.now() + durMs,
        expiredNotify: false,
      };

      rooms.set(roomId, room);
      currentRoomId = roomId;
      currentUser   = user;
      socket.join(roomId);

      socket.emit('room-created', {
        roomId,
        room: serialize(room),
      });

      console.log(`[+] Room ${roomId} created by ${name} (${userLimit} users / ${dur}${durationUnit[0]})`);
    } catch (e) {
      console.error('create-room:', e);
      emit_err('SERVER_ERROR', 'Failed to create room. Try again.');
    }
  });

  // ── JOIN ROOM ──────────────────────────────────────────────────────────────
  socket.on('join-room', ({ name, roomId }) => {
    try {
      name   = (name   || '').trim();
      roomId = (roomId || '').trim();

      if (!name)              return emit_err('INVALID_NAME',    'Please enter your name.');
      if (!/^\d{6}$/.test(roomId))
                              return emit_err('INVALID_ROOM_ID', 'Room ID must be exactly 6 digits.');

      const room = rooms.get(roomId);

      if (!room)              return emit_err('ROOM_NOT_FOUND',  'Room not found. Double-check the ID.');
      if (isExpired(room))    return emit_err('ROOM_EXPIRED',    'This room has expired. No new joins allowed.');
      if (isFull(room))       return emit_err('ROOM_FULL',       `Room is full (${room.limit}/${room.limit}).`);
      if (room.users.some(u => u.id === socket.id))
                              return emit_err('ALREADY_JOINED',  'You are already in this room.');

      const user = { id: socket.id, name };
      room.users.push(user);
      currentRoomId = roomId;
      currentUser   = user;
      socket.join(roomId);

      // Tell everyone else a new user arrived
      socket.to(roomId).emit('user-joined', { user, users: room.users });

      // Confirm to the joiner with full room state
      socket.emit('room-joined', { roomId, room: serialize(room) });

      console.log(`[+] ${name} joined ${roomId} (${room.users.length}/${room.limit})`);
    } catch (e) {
      console.error('join-room:', e);
      emit_err('SERVER_ERROR', 'Failed to join room. Try again.');
    }
  });

  // ── MESSAGE RELAY (no persistence) ────────────────────────────────────────
  socket.on('message', ({ content }) => {
    if (!currentRoomId || !currentUser) return;
    if (!content || !content.trim())    return;
    if (content.length > 4000)          return;

    io.to(currentRoomId).emit('message', {
      id        : crypto.randomUUID(),
      senderId  : socket.id,
      senderName: currentUser.name,
      content   : content.trim(),
      timestamp : Date.now(),
    });
  });

  // ── WebRTC SIGNALING ───────────────────────────────────────────────────────
  socket.on('signal', ({ to, signal, fromName }) => {
    if (!to || !signal) return;
    io.to(to).emit('signal', {
      from    : socket.id,
      fromName: fromName || currentUser?.name || 'Unknown',
      signal,
    });
  });

  socket.on('ice-candidate', ({ to, candidate }) => {
    if (!to || !candidate) return;
    io.to(to).emit('ice-candidate', { from: socket.id, candidate });
  });

  // ── VOICE CALL MANAGEMENT ─────────────────────────────────────────────────
  socket.on('join-call', ({ roomId }) => {
    const room = rooms.get(roomId);
    if (!room || !currentUser) return;

    // Snapshot existing callers BEFORE adding this user
    const members = [...room.callers]
      .filter(cid => cid !== socket.id)
      .map(cid => {
        const u = room.users.find(u => u.id === cid);
        return { id: cid, name: u?.name || 'Unknown' };
      });

    room.callers.add(socket.id);

    // Tell new joiner who's already in call → they will initiate P2P offers
    socket.emit('call-members', { members });

    // Announce to the rest of the room
    socket.to(roomId).emit('call-joined', {
      caller: { id: socket.id, name: currentUser.name },
    });

    console.log(`[📞] ${currentUser.name} joined call in ${roomId} (${room.callers.size} in call)`);
  });

  socket.on('leave-call', ({ roomId }) => {
    const room = rooms.get(roomId);
    if (room) room.callers.delete(socket.id);

    socket.to(roomId).emit('call-left', {
      userId  : socket.id,
      userName: currentUser?.name || 'Unknown',
    });
  });

  // ── DISCONNECT ────────────────────────────────────────────────────────────
  socket.on('disconnect', reason => {
    console.log(`[-] ${socket.id} disconnected (${reason})`);

    if (!currentRoomId || !currentUser) return;
    const room = rooms.get(currentRoomId);
    if (!room) return;

    room.users   = room.users.filter(u => u.id !== socket.id);
    room.callers.delete(socket.id);

    socket.to(currentRoomId).emit('user-left', {
      userId  : socket.id,
      userName: currentUser.name,
      users   : room.users,
    });

    socket.to(currentRoomId).emit('call-left', {
      userId  : socket.id,
      userName: currentUser.name,
    });

    // Clean up room if empty and expired
    if (room.users.length === 0 && isExpired(room)) {
      rooms.delete(currentRoomId);
    }
  });

  // ── Local helper ───────────────────────────────────────────────────────────
  function emit_err (code, message) {
    socket.emit('error', { code, message });
  }
});

// Serialize room (Sets → Arrays for JSON transport)
function serialize (room) {
  return {
    users    : room.users,
    limit    : room.limit,
    createdAt: room.createdAt,
    expiresAt: room.expiresAt,
  };
}

// ─── Start ───────────────────────────────────────────────────────────────────
server.listen(PORT, () => {
  console.log(`
╔══════════════════════════════════════════╗
║   HUNT AI  ·  Signaling Server           ║
║   Listening on port ${String(PORT).padEnd(20)}║
║   Built by axeroai                       ║
╚══════════════════════════════════════════╝`);
});
