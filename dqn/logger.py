import os
import torch
import torch.nn as nn


class Logger(object):
    def __init__(self, config):
        self.exp_name = config['experiment_name']
        self.log_name = self.exp_name + '.log'
        self.log_dir = config['log_dir']
        self.log_stdout = config['log_stdout']

        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
        if not config['recover']:
            log_file = open(self.log_dir + self.log_name, 'w+')
            log_file.write('{}\n'.format(self.exp_name))
            log_file.close()

        if self.log_stdout:
            print("Experiment: ", self.exp_name)

        self.eval_time_history = list()
        self.avg_reward_history = list()
        self.num_episode_history = list()

    def record(self, train_t: int, avg_reward: float, num_episode: int):
        self.eval_time_history.append(train_t)
        self.avg_reward_history.append(avg_reward)
        self.num_episode_history.append(num_episode)

        log_file = open(self.log_dir + self.log_name, 'a+')
        log_file.write('[{}, {}, {}]\n'.format(train_t, avg_reward, num_episode))
        log_file.close()

        if self.log_stdout:
            print('Evaluation at training step {}: average reward is {}, number of episode is {}'.format(train_t,
                                                                                                         avg_reward,
                                                                                                         num_episode))

    def save_model(self, model: nn.Module):
        torch.save(model.state_dict(), self.log_dir + self.exp_name + '.model')

    def recover(self, path, recover_step):
        log_file = open(self.log_dir + self.log_name, 'a+')
        log_file.write('Recover model from {}\n'.format(path))
        log_file.write('Recover training from step {}\n'.format(recover_step))
        log_file.close()

    def pretrain(self, path):
        log_file = open(self.log_dir + self.log_name, 'a+')
        log_file.write('Load pretrain model from {}\n'.format(path))
        log_file.close()

    def train_over(self):
        log_file = open(self.log_dir + self.log_name, 'a+')
        log_file.write('{}\n{}\n{}\n'.format(self.eval_time_history, self.avg_reward_history, self.num_episode_history))
        log_file.close()

