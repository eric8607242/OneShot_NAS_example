import os
import time

import torch

from utils import AverageMeter, accuracy, save
from ..base_training_agent import MetaTrainingAgent

class CFTrainingAgent(MetaTrainingAgent):
    """The training agent to train the supernet and the searched architecture.

    By implementing TrainingAgent class, users can adapt the searching and evaluating agent into
    various tasks easily.
    """
    @staticmethod
    def searching_evaluate(model, val_loader, device, criterion):
        """ Evaluating the performance of the supernet. The search strategy will evaluate
        the architectures by this static method to search.

        Args:
            model (nn.Module)
            val_loader (torch.utils.data.DataLoader)
            device (torch.device)
            criterion (nn.Module)

        Return:
            evaluate_metric (float): The performance of the supernet.
        """
        model.eval()

        top1 = AverageMeter()
        top5 = AverageMeter()
        losses = AverageMeter()

        with torch.no_grad():
            for step, (X, y) in enumerate(val_loader):
                X, y = X.to(device, non_blocking=True), \
                       y.to(device, non_blocking=True)
                N = X.shape[0]
                outs = model(X)

                loss = criterion(outs, y)
                prec1, prec5 = accuracy(outs, y, topk=(1, 5))

                losses.update(loss.item(), N)
                top1.update(prec1.item(), N)
                top5.update(prec5.item(), N)
        return top1.get_avg(), top5.get_avg(), losses.get_avg()


    def _training_step(self, model, train_loader, agent, epoch, print_freq=100):
        """
        Args:
            model (nn.Module)
            train_loader (torch.utils.data.DataLoader)
            agent (Object): The evaluate agent
            epoch (int)
        """
        top1 = AverageMeter()
        top5 = AverageMeter()
        losses = AverageMeter()

        model.train()
        start_time = time.time()

        for step, (X, y) in enumerate(train_loader):
            if agent.agent_state == "search":
                agent._iteration_preprocess()

            X, y = X.to(
                agent.device, non_blocking=True), y.to(
                agent.device, non_blocking=True)
            N = X.shape[0]

            agent.optimizer.zero_grad()
            outs = model(X)

            loss = agent.criterion(outs, y)
            loss.backward()

            agent.optimizer.step()
            agent.lr_scheduler.step()

            prec1, prec5 = accuracy(outs, y, topk=(1, 5))

            losses.update(loss.item(), N)
            top1.update(prec1.item(), N)
            top5.update(prec5.item(), N)

            if (step > 1 and step % print_freq == 0) or (step == len(train_loader) - 1):
                agent.logger.info(f"Train : [{(epoch+1):3d}/{agent.epochs}] "
                                 f"Step {step:3d}/{len(train_loader)-1:3d} Loss {losses.get_avg():.3f}"
                                 f"Prec@(1, 5) ({top1.get_avg():.1%}, {top5.get_avg():.1%})")

        agent.writer.add_scalar("Train/_loss/", losses.get_avg(), epoch)
        agent.writer.add_scalar("Train/_top1/", top1.get_avg(), epoch)
        agent.writer.add_scalar("Train/_top5/", top5.get_avg(), epoch)

        agent.logger.info(
            f"Train: [{epoch+1:3d}/{agent.epochs}] Final Loss {losses.get_avg():.3f}" 
            f"Final Prec@(1, 5) ({top1.get_avg():.1%}, {top5.get_avg():.1%})"
            f"Time {time.time() - start_time:.2f}")


    def _validate_step(self, model, val_loader, agent, epoch):
        """
        Args:
            model (nn.Module)
            val_loader (torch.utils.data.DataLoader)
            agent (Object): The evaluate agent
            epoch (int)

        Return:
            evaluate_metric (float): The performance of the searched model.
        """
        model.eval()
        start_time = time.time()

        top1_avg, top5_avg, losses_avg = self.searching_evaluate(model, val_loader, agent.device, agent.criterion)

        agent.writer.add_scalar("Valid/_loss/", losses_avg, epoch)
        agent.writer.add_scalar("Valid/_top1/", top1_avg, epoch)
        agent.writer.add_scalar("Valid/_top5/", top5_avg, epoch)

        agent.logger.info(
            f"Valid : [{epoch+1:3d}/{agent.epochs}] Final Loss {losses_avg:.3f}" 
            f"Final Prec@(1, 5) ({top1_avg:.1%}, {top5_avg:.1%})"
            f"Time {time.time() - start_time:.2f}")

        return top1_avg



