import torch
import torch.nn as nn
import torch.optim as optim
import numpy as np


class QNetwork(nn.Module):
    def __init__(self, env):
        super(QNetwork, self).__init__()
        self.lstm = nn.LSTM(input_size=env.n_observation, hidden_size=64, num_layers=1)
        self.fc_1 = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(True)
        )
        self.fc_2 = nn.Linear(32, env.n_action)

    def forward(self, state_in, hidden0, hidden1):
        hidden = (hidden0.unsqueeze(0), hidden1.unsqueeze(0))
        q_out, (new_hidden0, new_hidden1) = self.lstm(state_in.unsqueeze(0), hidden)
        q_out = self.fc_1(q_out)
        q_out = self.fc_2(q_out)
        return q_out.squeeze(0), (new_hidden0.squeeze(), new_hidden1.squeeze())


class QFunction(object):
    def __init__(self, env, device):
        self.q_network = QNetwork(env).to(device=device)
        self.optimizer = optim.Adam(self.q_network.parameters(), lr=0.001, eps=1e-08)

    # return argmax(q(s,a))
    def argmax(self, state, hidden0, hidden1):
        with torch.no_grad():
            q_s, new_hidden = self.q_network(state, hidden0, hidden1)
        q_max, q_argmax = q_s.max(1)
        return q_argmax.item(), new_hidden

    def max_batch(self, s_batch, h0_batch, h1_batch):
        with torch.no_grad():
            q_s, nh_batch = self.q_network(s_batch, h0_batch, h1_batch)
        q_max, q_argmax = q_s.max(1)
        return q_max

    # update network
    def update(self, s_batch, a_batch, h0_batch, h1_batch, target_batch):
        q_s, nh_batch = self.q_network(s_batch, h0_batch, h1_batch)
        est_batch = torch.gather(q_s, 1, torch.unsqueeze(a_batch, 1)).squeeze()
        loss = ((est_batch - target_batch) ** 2).mean()

        self.optimizer.zero_grad()
        loss.backward()
        self.optimizer.step()

    # load a network model
    def load_model(self, q_network):
        self.q_network.load_state_dict(q_network.state_dict())

    # load a network model from state dict
    def load_model_from_state_dict(self, state_dict):
        self.q_network.load_state_dict(state_dict)

    # retrieve the network model
    def get_model(self):
        return self.q_network


# DRQN Agent
class Agent(object):
    def __init__(self, env, device):
        self.device = device

        self.env = env
        self.q_func = QFunction(env, device)
        self.target_q_func = QFunction(env, device)
        self.target_q_func.load_model(self.q_func.get_model())

    # take action under epsilon-greedy policy
    def action(self, state, hidden0, hidden1, epsilon):
        s_tensor = torch.from_numpy(state).unsqueeze(0).to(device=self.device, dtype=torch.float)
        h0_tensor = hidden0.unsqueeze(0).to(device=self.device)
        h1_tensor = hidden1.unsqueeze(0).to(device=self.device)
        q_argmax, new_hidden = self.q_func.argmax(s_tensor, h0_tensor, h1_tensor)

        if np.random.uniform() <= epsilon:
            return np.random.randint(0, self.env.n_action), new_hidden
        else:
            return q_argmax, new_hidden

    # train the agent with a mini-batch of transition (s, h, a, r, s2, h2)
    # due to env we do not need "done" here
    def train(self, s_batch, h0_batch, h1_batch, a_batch, r_batch, s2_batch, h20_batch, h21_batch, gamma):
        # move tensors to training device and set data type of tensors
        s_batch = s_batch.to(device=self.device, dtype=torch.float)
        h0_batch = h0_batch.to(device=self.device)
        h1_batch = h1_batch.to(device=self.device)
        a_batch = a_batch.to(device=self.device)
        r_batch = r_batch.to(device=self.device)
        s2_batch = s2_batch.to(device=self.device, dtype=torch.float)
        h20_batch = h20_batch.to(device=self.device)
        h21_batch = h21_batch.to(device=self.device)

        target_batch = r_batch + gamma * self.target_q_func.max_batch(s2_batch, h20_batch, h21_batch)
        self.q_func.update(s_batch, a_batch, h0_batch, h1_batch, target_batch)

    # update target q function
    def update_target(self):
        self.target_q_func.load_model(self.q_func.get_model())

    # load a q model
    def load_model(self, q_network: nn.Module):
        self.q_func.load_model(q_network)
        self.target_q_func.load_model(q_network)

    # load a q model from state dict
    def load_model_from_state_dict(self, state_dict: dict):
        self.q_func.load_model_from_state_dict(state_dict)
        self.target_q_func.load_model_from_state_dict(state_dict)

    # retrieve q model
    def get_model(self):
        return self.q_func.get_model()
