import sls
import torch
import torchvision
import tqdm
import pandas as pd
import models
import datasets
import argparse

from torch.nn import functional as F
from torch.utils.data import DataLoader


def main(dataset_name, model_name):
    print("Dataset: %s - Model: %s - Optimizer: SgdArmijo" % (dataset_name, model_name))

    # Load Dataset
    train_set = datasets.get_dataset(dataset_name=dataset_name, datadir="./data")
    train_loader = DataLoader(train_set, drop_last=True, shuffle=True, batch_size=128)

    # Create model
    model = models.get_model(model_name).cuda()

    # Run Optimizer
    opt = sls.SgdArmijo(model.parameters(),
                         n_batches_in_epoch=len(train_loader))

    result_dict = []
    for epoch in range(5):
        # =================================
        # 1. Compute metrics over train loader
        model.eval()
        print("Evaluating Epoch %d" % epoch)

        loss_sum = 0.
        for images, labels in tqdm.tqdm(train_loader):
            images, labels = images.cuda(), labels.cuda()

            with torch.no_grad():
                loss_sum += compute_loss(model, images, labels)

        loss_avg = float(loss_sum / len(train_set))
        result_dict += [{"loss_avg":loss_avg, "epoch":epoch}]

        # =================================
        # 2. Train over train loader
        model.train()
        print("Training Epoch %d" % epoch)

        for images,labels in tqdm.tqdm(train_loader):
            images, labels = images.cuda(), labels.cuda()

            opt.zero_grad()
            closure = lambda : compute_loss(model, images, labels)
            opt.step(closure)

        print(pd.DataFrame(result_dict))


def compute_loss(model, images, labels):
    probs = F.log_softmax(model(images), dim=1)
    loss = F.nll_loss(probs, labels, reduction="sum")

    return loss


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-d", "--dataset_name", default="MNIST")
    parser.add_argument("-m", "--model_name", default="MLP")
    args = parser.parse_args()

    main(dataset_name=args.dataset_name, model_name=args.model_name)
