import re
import datetime
from sklearn.cluster import KMeans
import numpy as np

def str2date(s):
    # str -> date
    ptn = r'(\d+)/(\d+)/(\d+)'
    m = re.search(ptn, s)
    return datetime.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))


def get_scores_of_best_kmeans_model(sr, n_clusters, scores):
    models = []
    inertias = []
    for _ in range(5):
        kmeans = KMeans(n_clusters=n_clusters).fit(
            np.array(sr).reshape(-1, 1))
        # print(_, ':---------------')
        # print(kmeans.cluster_centers_)
        # print(kmeans.inertia_)
        # print(kmeans.n_iter_)
        inertias.append(kmeans.inertia_)
        models.append(kmeans)
    best_ = models[np.argmin(inertias)]
    tmp = list(enumerate(best_.cluster_centers_.reshape(-1)))
    tmp = sorted(tmp, key=lambda x: (x[1], x[0]))
    label2score = {tmp[i][0]: scores[i] for i in range(len(tmp))}
    return [label2score[each] for each in best_.labels_]