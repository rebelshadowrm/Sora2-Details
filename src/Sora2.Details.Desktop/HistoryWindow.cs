using System.Windows;
using System.Windows.Controls;
using System.Windows.Data;
using System.Windows.Media;
using Sora2.Details.Core;

namespace Sora2.Details.Desktop;

public sealed class HistoryWindow : Window
{
    private sealed record HistoryItem(Encounter Encounter, string Display, BossClassification Classification);
    private readonly IReadOnlyList<Encounter> _encounters;
    private readonly EncounterHistorySettings _settings;
    private readonly ListBox _list;
    private readonly Button _markBoss;
    private readonly Button _markRegular;
    private readonly Button _clearMark;
    public Encounter? SelectedEncounter => (_list.SelectedItem as HistoryItem)?.Encounter;

    public static string Describe(Encounter encounter, BossClassification classification) =>
        EncounterHistoryView.Describe(encounter, classification);

    internal HistoryWindow(IReadOnlyList<Encounter> encounters, EncounterHistorySettings settings)
    {
        _encounters = encounters;
        _settings = settings;
        Title = $"{EncounterHistoryView.FilterModeLabel(settings.FilterMode)} history";
        Width = 650;
        Height = 440;
        Background = new SolidColorBrush(Color.FromRgb(27, 30, 35));
        Foreground = Brushes.White;
        var panel = new DockPanel { Margin = new Thickness(14) };
        var filter = new ComboBox { Margin = new Thickness(0, 0, 0, 10), MinWidth = 230 };
        foreach (var (mode, tooltip) in new[]
        {
            (HistoryFilterMode.LikelyBosses,
                "Overconfident best effort: show confirmed bosses and name/+ candidates; hide unclassified fights."),
            (HistoryFilterMode.Confirmed,
                "Strict confirmation: only manual Boss marks count as confirmed. Fail-open keeps tentative and unknown fights visible; only marked Regular fights are hidden."),
            (HistoryFilterMode.Unfiltered,
                "Show every recorded fight, including fights marked Regular.")
        })
        {
            filter.Items.Add(new ComboBoxItem
            {
                Content = EncounterHistoryView.FilterModeLabel(mode),
                Tag = mode,
                ToolTip = tooltip
            });
        }
        filter.SelectedItem = filter.Items.Cast<ComboBoxItem>()
            .First(item => item.Tag is HistoryFilterMode mode && mode == settings.FilterMode);
        filter.SelectionChanged += (_, _) =>
        {
            if (filter.SelectedItem is ComboBoxItem { Tag: HistoryFilterMode mode }) SetFilterMode(mode);
        };
        DockPanel.SetDock(filter, Dock.Top);
        panel.Children.Add(filter);
        var actions = new StackPanel { Orientation = Orientation.Horizontal,
            Margin = new Thickness(0, 10, 0, 0) };
        _markBoss = new Button { Content = "Confirm boss", Padding = new Thickness(8),
            IsEnabled = false, ToolTip = "Confirm this encounter as a boss fight" };
        _markBoss.Click += (_, _) => MarkSelection(BossClassification.MarkedBoss);
        actions.Children.Add(_markBoss);
        _markRegular = new Button { Content = "Mark regular", Margin = new Thickness(8, 0, 0, 0),
            Padding = new Thickness(8), IsEnabled = false,
            ToolTip = "Hide this fight in Likely bosses and Confirmed modes; Unfiltered still shows it" };
        _markRegular.Click += (_, _) => MarkSelection(BossClassification.MarkedRegular);
        actions.Children.Add(_markRegular);
        _clearMark = new Button { Content = "Clear mark", Margin = new Thickness(8, 0, 0, 0),
            Padding = new Thickness(8), IsEnabled = false };
        _clearMark.Click += (_, _) => MarkSelection(BossClassification.Unclassified);
        actions.Children.Add(_clearMark);
        var open = new Button { Content = "Open encounter", Margin = new Thickness(10, 0, 0, 0),
            Padding = new Thickness(8) };
        open.Click += (_, _) => OpenSelection();
        actions.Children.Add(open);
        DockPanel.SetDock(actions, Dock.Bottom);
        panel.Children.Add(actions);
        _list = new ListBox
        {
            DisplayMemberPath = nameof(HistoryItem.Display),
            Background = new SolidColorBrush(Color.FromRgb(38, 42, 49)),
            Foreground = Brushes.White,
            BorderThickness = new Thickness(0)
        };
        var itemStyle = new Style(typeof(ListBoxItem));
        var bossStyle = new DataTrigger { Binding = new Binding(nameof(HistoryItem.Classification)),
            Value = BossClassification.MarkedBoss };
        bossStyle.Setters.Add(new Setter(Control.ForegroundProperty, Brushes.Gold));
        bossStyle.Setters.Add(new Setter(Control.FontWeightProperty, FontWeights.SemiBold));
        itemStyle.Triggers.Add(bossStyle);
        var catalogStyle = new DataTrigger { Binding = new Binding(nameof(HistoryItem.Classification)),
            Value = BossClassification.CatalogBossCandidate };
        catalogStyle.Setters.Add(new Setter(Control.ForegroundProperty, Brushes.Gold));
        itemStyle.Triggers.Add(catalogStyle);
        var miniStyle = new DataTrigger { Binding = new Binding(nameof(HistoryItem.Classification)),
            Value = BossClassification.PlusMiniBossCandidate };
        miniStyle.Setters.Add(new Setter(Control.ForegroundProperty, Brushes.LightGoldenrodYellow));
        itemStyle.Triggers.Add(miniStyle);
        _list.ItemContainerStyle = itemStyle;
        _list.SelectionChanged += (_, _) => RefreshMarkButtons();
        RefreshItems();
        _list.MouseDoubleClick += (_, _) => OpenSelection();
        panel.Children.Add(_list);
        Content = panel;
    }

    private void OpenSelection()
    {
        if (SelectedEncounter is not null) DialogResult = true;
    }

    private void SetFilterMode(HistoryFilterMode mode)
    {
        _settings.FilterMode = mode;
        Title = $"{EncounterHistoryView.FilterModeLabel(mode)} history";
        SaveSettings();
        RefreshItems();
    }

    private void MarkSelection(BossClassification mark)
    {
        if (SelectedEncounter is not { } encounter) return;
        if (mark == BossClassification.MarkedBoss) _settings.MarkBoss(encounter.Id);
        else if (mark == BossClassification.MarkedRegular) _settings.MarkRegular(encounter.Id);
        else _settings.ClearMark(encounter.Id);
        SaveSettings();
        RefreshItems(encounter.Id);
    }

    private void RefreshItems(string? selectedId = null)
    {
        selectedId ??= SelectedEncounter?.Id;
        _list.ItemsSource = EncounterHistoryView.Visible(_encounters, _settings.FilterMode,
                _settings.BossEncounterIds, _settings.RegularEncounterIds)
            .Select(encounter =>
            {
                var classification = EncounterHistoryView.Classify(encounter,
                    _settings.BossEncounterIds, _settings.RegularEncounterIds);
                return new HistoryItem(encounter, Describe(encounter, classification), classification);
            }).ToArray();
        _list.SelectedItem = _list.Items.Cast<HistoryItem>()
            .FirstOrDefault(item => item.Encounter.Id == selectedId);
        RefreshMarkButtons();
    }

    private void RefreshMarkButtons()
    {
        _markBoss.IsEnabled = SelectedEncounter is not null;
        _markRegular.IsEnabled = SelectedEncounter is not null;
        _clearMark.IsEnabled = SelectedEncounter is { } encounter &&
            (_settings.BossEncounterIds.Contains(encounter.Id) ||
             _settings.RegularEncounterIds.Contains(encounter.Id));
    }

    private void SaveSettings()
    {
        try { _settings.Save(); }
        catch (Exception exception) when (exception is System.IO.IOException or UnauthorizedAccessException)
        {
            MessageBox.Show(this, $"History preference could not be saved: {exception.Message}",
                "Encounter history", MessageBoxButton.OK, MessageBoxImage.Warning);
        }
    }
}
