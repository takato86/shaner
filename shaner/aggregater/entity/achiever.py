import logging
import numpy as np
import pandas as pd
import os
from shaner.utils import l2_norm_dist

logger = logging.getLogger(__name__)


class AbstractAchiever:
    def __init__(self, _range, n_obs):
        self._range = _range
        self.n_obs = n_obs

    def eval(self, obs, current_state):
        raise NotImplementedError

    def __generate_subgoals(self):
        raise NotImplementedError


class FourroomsAchiever(AbstractAchiever):
    def __init__(self, _range, n_obs, subgoals, **params):
        super().__init__(_range, n_obs)
        self.subgoals = subgoals  # 2d-ndarray shape(#obs, #subgoals)

    def eval(self, obs, current_state):
        if len(self.subgoals) <= current_state:
            return False
        subgoal = np.array(self.subgoals[current_state])
        return all(obs == subgoal)


class PinballAchiever(AbstractAchiever):
    def __init__(self, _range, n_obs, subgoals, **params):
        super().__init__(_range, n_obs)
        self.subgoals = subgoals # 2d-ndarray shape(#obs, #subgoals)

    def eval(self, obs, current_state):
        if len(self.subgoals) <= current_state:
            return False
        subgoal = np.array(self.subgoals[current_state])
        idxs = np.argwhere(subgoal == subgoal)  # np.nanでない要素を取り出し
        b_in = l2_norm_dist(subgoal[idxs].reshape(-1), obs[idxs].reshape(-1)) <= self._range
        res = np.all(b_in)
        if res:
            logger.debug("Achieve the subgoal{}".format(current_state))
        return res

    def __generate_subgoals(self):
        df = pd.read_csv(self.subgoal_path)
        subgoals = df.values
        return subgoals


class FetchPickAndPlaceAchiever(AbstractAchiever):
    def __init__(self, _range, n_obs, **params):
        super().__init__(_range, n_obs)
        self.subgoals = self.__generate_subgoals()  # n_obs=25

    def eval(self, obs, current_state):
        if len(self.subgoals) <= current_state:
            return False
        subgoal = np.array(self.subgoals[current_state])
        idxs = np.argwhere(subgoal == subgoal) # np.nanでない要素を取り出し
        b_lower = subgoal[idxs] - self._range <= obs[idxs]
        b_higher = obs[idxs] <= subgoal[idxs] + self._range
        res = all(b_lower & b_higher)
        if res:
            logger.info("Achieve the subgoal{}".format(current_state))
        return res

    def __generate_subgoals(self):
        # Subgoal1: Objectの絶対座標[x,y,z] = achieved_goal
        # Subgoal2: Objectの絶対座標とArmの位置が同じでアームを閉じている状態。
        subgoal1 = np.full(self.n_obs, np.nan)
        # subgoal1[6:8] = [0, 0]
        subgoal1[6:9] = [0, 0, 0]
        subgoal2 = np.full(self.n_obs, np.nan)
        # subgoal2[6:9] = [0, 0, 0]
        subgoal2[6:11] = [0, 0, 0, 0.02, 0.02]
        return [subgoal1, subgoal2]


class CrowdSimAchiever(AbstractAchiever):
    def __init__(self, _range, n_obs, **params):
        super().__init__(_range, n_obs)
        self.subgoals = self.__generate_subgoals()
    
    def eval(self, state, current_state):
        # state: JointState: self_state, human_states
        import pdb; pdb.set_trace()
        if current_state >= len(self.subgoals):
            return False
        

    def __generate_subgoals(self):
        # 相対座標により指定
        # v_rとv_hの差分のcosが1；直角に交わるかつ、robotがcell_sizeよりhumanの後ろを通る。
        return [
            {
                "relative_velocity_angle": 0,  # 相対角度
                "dist": 2  # 人のpositionを原点とした相対座標
            }
        ]
        