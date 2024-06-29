import express from 'express';
import { config } from 'dotenv';
import { connectDb } from './config/mongo.js';
import { router_channel } from './routes/channels.router.js';
import { router_user } from './routes/users.router.js';
import { router_post } from './routes/posts.router.js';
import http from 'http';
import { Server } from 'socket.io';
import cors from 'cors';
import { chatModel } from './models/chat.model.js';
import { router_notifications } from './routes/notifications.router.js';
import { userModel } from './models/user.model.js';
import { router_chat } from './routes/chat.router.js';
import { router_shortcut } from './routes/shortcut.router.js';
import { router_web } from './routes/web.router.js';
import { newestMessageModel } from './models/newestMessage.model.js';
import { router_crawl } from './routes/crawl.router.js';
config();
connectDb();
const port = process.env.PORT || 3000;
const app = express();
const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: 'http://localhost:5173',
    methods: ['GET', 'POST'],
  },
});
app.use(cors());
app.use('/public', express.static('public'));
app.use(router_channel);
app.use(router_user);
app.use(router_post);
app.use(router_notifications);
app.use(router_chat);
app.use(router_shortcut);
app.use(router_web);
app.use(router_crawl);

io.on('connection', (socket) => {
  socket.on('joinCall', async (user) => {
    await userModel.findByIdAndUpdate(user._id, { socketCallId: socket.id });
  });

  socket.on('callUser', async ({ signalData, seeder, receiver }) => {
    const receiverUser = await userModel.findById(receiver?._id);
    if (receiverUser) {
      io.to(receiverUser.socketCallId).emit('callUser', {
        signal: signalData,
        from: seeder,
      });
    }
  });

  socket.on('answerCall', async (data) => {
    const receiverUser = await userModel.findById(data.to._id);
    if (receiverUser) {
      io.to(receiverUser.socketCallId).emit('callAccepted', data.signal);
    }
  });
  socket.on('callEnd', async ({ receiver }) => {
    const receiverUser = await userModel.findById(receiver._id);
    if (receiverUser) {
      io.to(receiverUser.socketCallId).emit('callEnd', {
        receiver: receiverUser,
      });
    }
  });
  socket.on('joinChat', async (user) => {
    await userModel.findByIdAndUpdate(user._id, { socketId: socket.id });
  });

  socket.on('sendMessage', async (data) => {
    const { sender, receiver, content, lastSent } = data;
    const newMessage = new chatModel({
      sender: sender._id,
      receiver: receiver._id,
      content: content,
    });
    const existedMessage = await newestMessageModel.findOne({
      $or: [
        {
          'sender.user': sender._id,
          'receiver.user': receiver._id,
        },
        {
          'sender.user': receiver._id,
          'receiver.user': sender._id,
        },
      ],
    });
    if (!existedMessage) {
      const newestMessage = new newestMessageModel({
        sender: {
          user: sender._id,
          isRead: true,
        },
        receiver: {
          user: receiver._id,
          isRead: false,
        },
        content: content,
        lastSent: lastSent._id,
      });
      await newestMessage.save();
    } else {
      if (existedMessage?.sender?.user.toString() === sender._id) {
        await newestMessageModel.findOneAndUpdate(
          {
            'sender.user': sender._id,
            'receiver.user': receiver._id,
          },
          {
            'sender.user': sender._id,
            'sender.isRead': true,
            'receiver.user': receiver._id,
            'receiver.isRead': false,
            lastSent: sender._id,
            content: content,
            updated_at: Date.now(),
          }
        );
      }
      if (existedMessage?.receiver?.user.toString() === sender._id) {
        await newestMessageModel.findOneAndUpdate(
          {
            'sender.user': receiver._id,
            'receiver.user': sender._id,
          },
          {
            'sender.user': receiver._id,
            'sender.isRead': false,
            'receiver.user': sender._id,
            'receiver.isRead': true,
            lastSent: sender._id,
            content: content,
            updated_at: Date.now(),
          }
        );
      }
    }
    await newMessage.save();
    socket.emit('receiveMessage', { ...data, refetch: true });
    const receiverUser = await userModel.findById(receiver._id);
    if (receiverUser) {
      io.to(receiverUser.socketId).emit('receiveMessage', {
        ...data,
        refetch: true,
      });
    }
  });

  socket.on('disconnect', async () => {
    await userModel.findOneAndUpdate(
      { socketId: socket.id },
      { socketId: null }
    );
    console.log('Client disconnected');
  });
});

server.listen(port, () => {
  console.log(`App listening on port ${port}`);
});
