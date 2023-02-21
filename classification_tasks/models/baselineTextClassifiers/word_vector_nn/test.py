import os

import torch
from datasets import load_data
from torch import nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from utils import AverageMeter, load_checkpoint, parse_opt

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def test(model: nn.Module, model_name: str, test_loader: DataLoader) -> None:
    # track metrics
    accs = AverageMeter()  # accuracies

    # evaluate in batches
    with torch.no_grad():
        for i, batch in enumerate(tqdm(test_loader, desc="Evaluating")):
            if model_name in ["han"]:
                documents, sentences_per_document, words_per_sentence, labels = batch

                documents = documents.to(
                    device
                )  # (batch_size, sentence_limit, word_limit)
                sentences_per_document = sentences_per_document.squeeze(1).to(
                    device
                )  # (batch_size)
                words_per_sentence = words_per_sentence.to(
                    device
                )  # (batch_size, sentence_limit)
                labels = labels.squeeze(1).to(device)  # (batch_size)

                # forward
                scores, word_alphas, sentence_alphas = model(
                    documents, sentences_per_document, words_per_sentence
                )  # (n_documents, n_classes),
                # (n_documents, max_doc_len_in_batch, max_sent_len_in_batch),
                # (n_documents, max_doc_len_in_batch)

            else:
                sentences, words_per_sentence, labels = batch

                sentences = sentences.to(device)  # (batch_size, word_limit)
                words_per_sentence = words_per_sentence.squeeze(1).to(
                    device
                )  # (batch_size)
                labels = labels.squeeze(1).to(device)  # (batch_size)

                # for torchtext
                # sentences = batch.text[0].to(device)  # (batch_size, word_limit)
                # words_per_sentence = batch.text[1].to(device)  # (batch_size)
                # labels = batch.label.to(device)  # (batch_size)

                scores = model(sentences, words_per_sentence)  # (batch_size, n_classes)

            # accuracy
            _, predictions = scores.max(dim=1)  # (n_documents)
            correct_predictions = torch.eq(predictions, labels).sum().item()
            accuracy = correct_predictions / labels.size(0)

            # keep track of metrics
            accs.update(accuracy, labels.size(0))

        # final test accuracy
        print("\n * TEST ACCURACY - %.1f percent\n" % (accs.avg * 100))


if __name__ == "__main__":
    config = parse_opt()

    # load model
    checkpoint_path = os.path.join(
        config.checkpoint_path, config.checkpoint_basename + ".pth.tar"
    )
    model, _, _, _, _, _ = load_checkpoint(checkpoint_path, device)
    model = model.to(device)
    model.eval()

    # load test data
    test_loader = load_data(config, "test")

    test(model, config.model_name, test_loader)
