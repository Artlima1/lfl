import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import make_interp_spline

class LeagueChart:
    def __init__(self, filename='performance_chart.png'):
        self.filename = filename
        pass

    def export(self):
        pass

    def get_figure(self):
        """Returns the matplotlib figure object for display in Streamlit"""
        pass

class LeagueBoxPlot(LeagueChart):
    def __init__(self, scores_df, league_df, filename='boxplot.png'):
        super().__init__(filename)
        self.data = [scores_df[scores_df['roster_id'] == rid]['points'].values for rid in league_df['roster_id']]
        self.names = league_df['short_name'].values

    def get_figure(self):
        """Returns the matplotlib figure object for display"""
        fig = plt.figure(figsize=(10, 7))
        # Creating axes instance
        ax = fig.add_axes([0, 0, 1, 1])
        # Creating plot
        bp = ax.boxplot(self.data)
        # show plot
        plt.title("Boxplot de Pontuação")
        plt.xticks(range(1, len(self.names)+1), self.names, rotation=90)
        return fig

    def export(self):
        fig = self.get_figure()
        plt.savefig(self.filename, bbox_inches='tight')
        plt.close()

class LeaguePerformanceChart(LeagueChart):
    def __init__(self, league_df, filename='performance_chart.png'):
        super().__init__(filename)
        self.data = league_df.sort_values(by=['avg']).reset_index(drop=True)

    def get_figure(self):
        """Returns the matplotlib figure object for display"""
        fig = plt.figure(figsize=(10, 6))
        plt.errorbar(self.data['short_name'], self.data['avg'], yerr=self.data['std'], fmt='o', color='Black', elinewidth=3, capthick=3, errorevery=1, alpha=1, ms=4, capsize=5)
        plt.bar(self.data['short_name'], self.data['avg'], tick_label=self.data['short_name'])  # Bar plot
        plt.ylim((70, 165))
        plt.xlabel('TEAM')  # Label on X axis
        plt.xticks(rotation=90)
        plt.ylabel('Average Performance')  # Label on Y axis
        return fig

    def export(self):
        fig = self.get_figure()
        plt.savefig(self.filename, bbox_inches='tight')
        plt.close()

class LeagueExpWChart(LeagueChart):
    def __init__(self, league_df, filename='expw_chart.png'):
        super().__init__(filename)
        self.data = league_df.sort_values(by=['wins', 'exp_w'])
        self.data = self.data.reset_index(drop=True)

    def get_figure(self):
        """Returns the matplotlib figure object for display"""
        fig, ax = plt.subplots()
        ax.bar(self.data['short_name'], self.data['wins'], 0.8, label='Wins', color='b')
        ax.bar(self.data['short_name'], self.data['exp_w'], 0.3, label='Expected Wins', color='c')
        ax.set_ylabel('n° of wins')
        ax.set_title('Actual Wins & Expected Wins')
        ax.legend()
        plt.xticks(rotation=90)
        return fig

    def export(self):
        fig = self.get_figure()
        plt.savefig(self.filename, bbox_inches='tight')
        plt.close()

class LeagueProbChart(LeagueChart):
    def __init__(self, prob_df, league_df, team_names, filename='prob_chart.png'):
        super().__init__(filename)
        self.prob_df = prob_df
        self.league_df = league_df
        self.team_names = team_names

    def get_figure(self):
        """Returns the matplotlib figure object for display"""
        fig = plt.figure(figsize=(10, 6))

        # Iterate over each specified team
        for short_name in self.team_names:
            # Get roster_id for this team
            team_data = self.league_df[self.league_df['short_name'] == short_name]

            roster_id = team_data['roster_id'].values[0]
            wins = team_data['wins'].values[0]

            # Get probability data for this team
            team_prob = self.prob_df[self.prob_df['roster_id'] == roster_id].sort_values('n_wins')
            x_original = team_prob['n_wins'].values
            data = team_prob['prob'].values

            # Create a smooth x range for interpolation
            x_smooth = np.linspace(x_original.min(), x_original.max(), 200)

            # Create a cubic spline interpolation
            spline = make_interp_spline(x_original, data, k=2)
            y_smooth = spline(x_smooth)

            # Plot the smoothed curve
            line, = plt.plot(x_smooth, y_smooth, label=short_name)

            # Add a circle marker at the actual wins position
            y_wins = spline(wins)
            plt.plot(wins, y_wins, 'o', color=line.get_color(), markersize=8)

        # Final plot adjustments
        plt.title("Probabilidade para N vitórias")
        plt.xlabel("Número de Vitórias")
        plt.ylabel("Probabilidade")
        plt.legend()
        return fig

    def export(self):
        fig = self.get_figure()
        plt.savefig(self.filename, bbox_inches='tight')
        plt.close()